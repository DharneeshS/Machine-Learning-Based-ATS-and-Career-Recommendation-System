from .core import SkillRecommender
from .nlp_utils import find_similar_job_titles
from .config import Config
import sys

def display_recommendations(recommendations, match_percentage):
    """Display recommendations in a user-friendly format"""
    print(f"\nSkill Match: {match_percentage:.1f}%")
    print("=" * 80)
    
    if not recommendations:
        print("\nNo courses needed - you're already qualified!")
        return
        
    print("\nTop Recommended Courses:")
    for i, rec in enumerate(recommendations, 1):
        print(f"\n{i}. {rec['course']} ({rec['platform']})")
        print(f"   - Teaches: {rec['skill']} (Level: {rec['level']})")
        print(f"   - Duration: {rec['duration']}")
        print(f"   - URL: {rec['url']}")
    print("=" * 80)

def main():
    """Main interactive CLI interface"""
    try:
        recommender = SkillRecommender()
        
        print("\nJob Skills Recommender System")
        print("=" * 80)
        
        while True:
            job_title = input("\nEnter job title (or 'quit' to exit): ").strip()
            if job_title.lower() in ('quit', 'exit'):
                break
                
            # Get required skills
            required_skills = recommender.get_required_skills(job_title)
            
            # Handle unknown job titles
            if not required_skills:
                similar_jobs = find_similar_job_titles(job_title)
                if similar_jobs:
                    print("\nJob title not found. Similar titles:")
                    for i, (title, score) in enumerate(similar_jobs, 1):
                        print(f"{i}. {title} ({score:.0%} match)")
                    
                    choice = input("\nSelect a number or press Enter to try again: ")
                    if choice.isdigit() and 0 < int(choice) <= len(similar_jobs):
                        job_title = similar_jobs[int(choice)-1][0]
                        required_skills = recommender.get_required_skills(job_title)
                else:
                    print("\nJob title not found. Please try again.")
                    continue
            
            # Process skills
            if required_skills:
                print(f"\nRequired skills for {job_title}:")
                print(", ".join(required_skills))
                
                current_skills = input("\nEnter your current skills (comma separated): ").strip()
                current_skills = [s.strip() for s in current_skills.split(',')] if current_skills else []
                
                # Generate and display recommendations
                recommendations = recommender.recommend_courses(required_skills, current_skills)
                match_percentage = recommender.calculate_match_percentage(required_skills, current_skills)
                
                display_recommendations(recommendations, match_percentage)
                
                input("\nPress Enter to continue...")
            else:
                print("\nNo skills data available for this job title.")
                
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()