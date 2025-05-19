import os
from pathlib import Path

class Config:
    # Base configuration with absolute paths
    BASE_DATA_DIR = Path(r'C:\New Updated Code\Career_recommendation\data')
    
    # File paths
    DB_PATH = BASE_DATA_DIR / 'job_skills.db'
    COURSES_PATH = BASE_DATA_DIR / 'course_database.csv'
    SKILL_ALIASES_PATH = BASE_DATA_DIR / 'skill_aliases.json'
    MODEL_NAME = 'all-MiniLM-L6-v2'
    
    @classmethod
    def verify_paths(cls):
        """Verify all data files exist at application startup"""
        required_files = {
            'Database': cls.DB_PATH,
            'Courses CSV': cls.COURSES_PATH,
            'Skill Aliases': cls.SKILL_ALIASES_PATH
        }
        
        missing_files = []
        for name, path in required_files.items():
            if not path.exists():
                missing_files.append(f"{name}: {str(path)}")
        
        if missing_files:
            raise FileNotFoundError(
                "Missing required data files:\n" + 
                "\n".join(missing_files) +
                "\nPlease ensure all data files are in the correct location."
            )

# Verify paths when module is imported
Config.verify_paths()