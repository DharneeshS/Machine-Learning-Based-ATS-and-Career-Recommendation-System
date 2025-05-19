from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import sqlite3
import json
from .config import Config
import re
import os
import tempfile

# For handling different document types
import PyPDF2
import docx
import spacy
import nltk
from nltk.corpus import stopwords

# Initialize lazy-loaded resources
model = None
nlp = None
stop_words = None

def load_model():
    """Lazy-load the sentence transformer model"""
    global model
    if model is None:
        model = SentenceTransformer(Config.MODEL_NAME)
    return model

def load_spacy():
    """Lazy-load spaCy model"""
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            nlp = spacy.load("en_core_web_sm")
    return nlp

def load_nltk_resources():
    """Lazy-load NLTK resources"""
    global stop_words
    if stop_words is None:
        try:
            stop_words = set(stopwords.words('english'))
        except LookupError:
            nltk.download('stopwords')
            stop_words = set(stopwords.words('english'))
    return stop_words

def load_skill_aliases():
    """Load skill aliases with error handling"""
    try:
        with open(Config.SKILL_ALIASES_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        raise RuntimeError(f"Failed to load skill aliases: {str(e)}")

def enhanced_normalize_skill(skill, threshold=0.7):
    """Normalize skill name using semantic matching"""
    try:
        model = load_model()
        skill_aliases = load_skill_aliases()
        
        skill_lower = skill.lower().strip()
        if skill_lower in skill_aliases:
            return skill_aliases[skill_lower]
            
        skill_embedding = model.encode([skill_lower])
        known_skills = list(skill_aliases.keys())
        known_embeddings = model.encode(known_skills)
        
        similarities = cosine_similarity(skill_embedding, known_embeddings)[0]
        max_idx = similarities.argmax()
        
        return skill_aliases[known_skills[max_idx]] if similarities[max_idx] > threshold else skill.title()
    except Exception as e:
        print(f"Error normalizing skill '{skill}': {str(e)}")
        return skill.title()

def get_all_job_titles():
    """Fetch all job titles from database"""
    try:
        with sqlite3.connect(str(Config.DB_PATH)) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT title FROM job_requirements")
            return [row[0] for row in cursor.fetchall()]
    except Exception as e:
        raise RuntimeError(f"Database error: {str(e)}")

def find_similar_job_titles(query, threshold=0.7, top_n=3):
    """Find similar job titles using semantic search"""
    try:
        model = load_model()
        titles = get_all_job_titles()
        if not titles:
            return []
            
        title_embeddings = model.encode(titles)
        query_embedding = model.encode([query.lower()])
        
        similarities = cosine_similarity(query_embedding, title_embeddings)[0]
        top_indices = np.argsort(similarities)[-top_n:][::-1]
        
        return [(titles[i], float(similarities[i])) for i in top_indices if similarities[i] > threshold]
    except Exception as e:
        print(f"Error finding similar jobs: {str(e)}")
        return []

def get_known_skills():
    """Get a list of all known skills from the aliases"""
    try:
        skill_aliases = load_skill_aliases()
        # Get both the keys (raw skills) and values (normalized skills)
        all_skills = set(skill_aliases.keys()) | set(skill_aliases.values())
        return list(all_skills)
    except Exception as e:
        print(f"Error loading known skills: {str(e)}")
        return []

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file"""
    text = ""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + " "
    except Exception as e:
        print(f"Error extracting text from PDF: {str(e)}")
    return text

def extract_text_from_docx(file_path):
    """Extract text from a DOCX file"""
    text = ""
    try:
        doc = docx.Document(file_path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + " "
    except Exception as e:
        print(f"Error extracting text from DOCX: {str(e)}")
    return text

def extract_text_from_txt(file_path):
    """Extract text from a plain text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except UnicodeDecodeError:
        # Try with different encoding if UTF-8 fails
        try:
            with open(file_path, 'r', encoding='latin-1') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {str(e)}")
            return ""
    except Exception as e:
        print(f"Error reading text file: {str(e)}")
        return ""

def extract_text_from_file(file_path):
    """Extract text from various file formats"""
    file_extension = os.path.splitext(file_path)[1].lower()
    
    if file_extension == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_extension == '.docx':
        return extract_text_from_docx(file_path)
    elif file_extension == '.txt':
        return extract_text_from_txt(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")

def find_skills_in_text(text, threshold=0.6):
    """Extract skills from text using NLP and semantic matching"""
    # Load resources
    nlp = load_spacy()
    stop_words = load_nltk_resources()
    model = load_model()
    
    # Get known skills for matching
    known_skills = get_known_skills()
    known_embeddings = model.encode(known_skills)
    
    # Clean text
    text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Extract skill phrases using patterns and NLP
    potential_skills = set()
    
    # Method 1: Extract noun phrases using spaCy
    doc = nlp(text)
    for chunk in doc.noun_chunks:
        if len(chunk.text.split()) <= 4:  # Limit to phrases with 4 or fewer words
            potential_skills.add(chunk.text.strip())
    
    # Method 2: Look for common technical skills patterns
    skill_patterns = [
        r'\b[a-zA-Z]+\+{2}\b',  # C++, C#
        r'\b[a-zA-Z]+\#\b',      # C#
        r'\b[a-zA-Z]+\.js\b',    # Node.js, React.js
        r'\b[a-zA-Z]+\.[a-zA-Z]+\b',  # .NET, ASP.NET
    ]
    
    for pattern in skill_patterns:
        matches = re.findall(pattern, text)
        potential_skills.update(matches)
    
    # Filter out stop words and very short terms
    filtered_skills = []
    for skill in potential_skills:
        tokens = skill.split()
        if not all(token in stop_words for token in tokens) and len(skill) > 2:
            filtered_skills.append(skill)
    
    # Use semantic matching to find the most relevant skills
    matched_skills = set()
    
    # Direct matching
    for skill in filtered_skills:
        for known_skill in known_skills:
            if skill.lower() == known_skill.lower():
                normalized = enhanced_normalize_skill(skill)
                if normalized:
                    matched_skills.add(normalized)
                break
    
    # Semantic matching for remaining skills
    remaining_skills = [s for s in filtered_skills if not any(s.lower() == k.lower() for k in known_skills)]
    if remaining_skills:
        skill_embeddings = model.encode(remaining_skills)
        
        for i, skill_embedding in enumerate(skill_embeddings):
            similarities = cosine_similarity([skill_embedding], known_embeddings)[0]
            max_idx = similarities.argmax()
            
            if similarities[max_idx] > threshold:
                normalized = enhanced_normalize_skill(known_skills[max_idx])
                if normalized:
                    matched_skills.add(normalized)
    
    return list(matched_skills)

def extract_skills_from_resume(file_path):
    """Extract skills from a resume file"""
    try:
        # Extract text from the file
        text = extract_text_from_file(file_path)
        if not text:
            return []
        
        # Find skills in the extracted text
        skills = find_skills_in_text(text)
        
        # Return normalized and deduplicated skills
        return sorted(list(set(skills)))
    except Exception as e:
        print(f"Error extracting skills from resume: {str(e)}")
        return []