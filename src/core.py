import sqlite3
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from .config import Config
from .nlp_utils import enhanced_normalize_skill

class SkillRecommender:
    def __init__(self):
        """Initialize with data validation"""
        try:
            self.course_db = pd.read_csv(Config.COURSES_PATH)
            self.skill_aliases = self._load_skill_aliases()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize recommender: {str(e)}")
    
    def _load_skill_aliases(self):
        """Load skill aliases with validation"""
        aliases = {}
        with open(Config.SKILL_ALIASES_PATH, 'r') as f:
            import json
            aliases = json.load(f)
        
        if not isinstance(aliases, dict):
            raise ValueError("Skill aliases should be a dictionary")
        return aliases
    
    def get_required_skills(self, job_title):
        """Get skills for a job title from database"""
        try:
            with sqlite3.connect(str(Config.DB_PATH)) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT skills FROM job_requirements WHERE LOWER(title) = ?",
                    (job_title.lower(),)
                )
                result = cursor.fetchone()
                return result[0].split(', ') if result else None
        except Exception as e:
            print(f"Error fetching skills: {str(e)}")
            return None
    
    def recommend_courses(self, required_skills, current_skills=None, top_n=5):
        """Generate personalized course recommendations"""
        try:
            if not required_skills:
                return []
                
            norm_required = [enhanced_normalize_skill(s) for s in required_skills]
            norm_current = [enhanced_normalize_skill(s) for s in current_skills] if current_skills else []
            
            # Calculate skill gaps
            skill_gaps = list(set(norm_required) - set(norm_current))
            if not skill_gaps:
                return []  # No gaps found
            
            # Vectorize skills for relevance scoring
            vectorizer = TfidfVectorizer()
            all_skills = norm_required + norm_current
            skill_matrix = vectorizer.fit_transform(all_skills)
            
            recommendations = []
            for _, course in self.course_db.iterrows():
                if course['skill'] in skill_gaps:
                    skill_idx = all_skills.index(course['skill'])
                    relevance = 1.0  # Base relevance
                    
                    if norm_current:
                        curr_indices = [all_skills.index(s) for s in norm_current]
                        relevance += linear_kernel(
                            skill_matrix[skill_idx:skill_idx+1],
                            skill_matrix[curr_indices]
                        ).mean()
                    
                    course_data = course.to_dict()
                    course_data['relevance_score'] = relevance
                    recommendations.append(course_data)
            
            # Return top N most relevant courses
            return sorted(recommendations, 
                        key=lambda x: x['relevance_score'], 
                        reverse=True)[:top_n]
            
        except Exception as e:
            print(f"Error generating recommendations: {str(e)}")
            return []
    
    def calculate_match_percentage(self, required_skills, current_skills=None):
        """Calculate skill match percentage"""
        try:
            if not required_skills:
                return 0.0
                
            norm_required = [enhanced_normalize_skill(s) for s in required_skills]
            norm_current = [enhanced_normalize_skill(s) for s in current_skills] if current_skills else []
            
            matched = set(norm_required) & set(norm_current)
            return (len(matched) / len(norm_required)) * 100
        except Exception as e:
            print(f"Error calculating match: {str(e)}")
            return 0.0
        