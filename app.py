import streamlit as st
import matplotlib.pyplot as plt
from src.core import SkillRecommender
from src.nlp_utils import find_similar_job_titles, extract_skills_from_resume
import pandas as pd
import os
import tempfile

# Configure page
st.set_page_config(page_title="Job Skills Recommender", layout="wide")

# Initialize recommender
recommender = SkillRecommender()

# Load course data from CSV
course_data = pd.read_csv(r'C:\New Updated Code\Career_recommendation\data\course_database.csv')  # Update with your CSV file path

# Custom CSS for better styling
st.markdown("""
<style>
    .match-percentage {
        font-size: 24px !important;
        color: #4CAF50 !important;
        font-weight: bold !important;
    }
    .chart-container {
        margin-top: 20px;
        margin-bottom: 30px;
    }
    .course-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .course-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .course-title {
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
        color: #1a73e8;
    }
    .course-instructor {
        font-size: 14px;
        color: #5f6368;
        margin-bottom: 8px;
    }
    .course-rating {
        display: inline-block;
        background-color: #fbbc04;
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 8px;
    }
    .course-enrolled {
        font-size: 12px;
        color: #5f6368;
        display: inline-block;
    }
    .badge {
        display: inline-block;
        background-color: #e8f0fe;
        color: #1a73e8;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        margin-right: 8px;
        margin-bottom: 8px;
    }
    .upload-section {
        border: 2px dashed #1a73e8;
        border-radius: 10px;
        padding: 20px;
        margin-top: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .or-divider {
        display: flex;
        align-items: center;
        text-align: center;
        margin: 15px 0;
    }
    .or-divider::before, .or-divider::after {
        content: '';
        flex: 1;
        border-bottom: 1px solid #e0e0e0;
    }
    .or-divider span {
        padding: 0 10px;
        color: #5f6368;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)

# UI Components
st.title("🎯 AI-Powered Job Skills Recommender")

# Input Section
col1, col2 = st.columns(2)
with col1:
    job_title = st.text_input("Enter Job Title", placeholder="e.g., Data Scientist")

# Session state to store extracted skills
if 'extracted_skills' not in st.session_state:
    st.session_state.extracted_skills = []

with col2:
    # Input skills manually or extract from resume
    st.write("Your Current Skills")
    
    # Manual input option
    current_skills = st.text_input("Enter Skills (comma separated)", 
                                 placeholder="e.g., Python, SQL, Machine Learning",
                                 value=', '.join(st.session_state.extracted_skills) if st.session_state.extracted_skills else "")
    
    # OR divider
    st.markdown("<div class='or-divider'><span>OR</span></div>", unsafe_allow_html=True)
    
    # Resume upload option
    st.markdown("<div class='upload-section'>", unsafe_allow_html=True)
    st.write("📄 Upload your resume to extract skills")
    uploaded_file = st.file_uploader("Choose a file", type=['pdf', 'docx', 'txt'])
    
    if uploaded_file is not None:
        # Create a temporary file to store the uploaded content
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            temp_file.write(uploaded_file.getvalue())
            temp_file_path = temp_file.name
        
        try:
            # Extract skills from the resume
            with st.spinner("Extracting skills from resume..."):
                extracted_skills = extract_skills_from_resume(temp_file_path)
                st.session_state.extracted_skills = extracted_skills
                
                if extracted_skills:
                    st.success(f"✅ {len(extracted_skills)} skills extracted from your resume!")
                    # Update the text input with extracted skills
                    current_skills = ', '.join(extracted_skills)
                else:
                    st.warning("No skills were detected in the uploaded resume.")
        except Exception as e:
            st.error(f"Error extracting skills: {str(e)}")
        finally:
            # Clean up the temporary file
            os.unlink(temp_file_path)
    
    st.markdown("</div>", unsafe_allow_html=True)

def create_course_card(course):
    """Generate a styled course card with a link"""
    st.markdown(f"""
    <div class="course-card">
        <a href="{course['url']}" target="_blank" class="course-title">{course['course']}</a>
        <div class="course-instructor">{course.get('instructor', 'Unknown Instructor')}</div>
        <div>
            <span class="course-rating">★ {course.get('rating', '4.5')}</span>
            <span class="course-enrolled">{course.get('enrolled', '1M+')} learners</span>
        </div>
        <div>
            <span class="badge">{course['platform']}</span>
            <span class="badge">{course['level']}</span>
            <span class="badge">{course['duration']}</span>
        </div>
        <!-- Removed price section -->
    </div>
    """, unsafe_allow_html=True)

# Recommendation Logic
if st.button("Get Recommendations"):
    if job_title:
        with st.spinner("Analyzing skills..."):
            required_skills = recommender.get_required_skills(job_title)
            
            if not required_skills:
                similar_jobs = find_similar_job_titles(job_title)
                if similar_jobs:
                    st.warning(f"Job title not found. Did you mean: *{similar_jobs[0][0]}*?")
                    required_skills = recommender.get_required_skills(similar_jobs[0][0])
            
            if required_skills:
                current_skills_list = [s.strip() for s in current_skills.split(",")] if current_skills else []
                recommendations = recommender.recommend_courses(required_skills, current_skills_list)
                match_percentage = recommender.calculate_match_percentage(required_skills, current_skills_list)
                
                # Display Results with Pie Chart
                st.markdown(f"<div class='match-percentage'>🔍 Your skills match <span style='color:#4CAF50'>{match_percentage:.1f}%</span> of requirements for <span style='color:#1E88E5'>{job_title}</span></div>", 
                           unsafe_allow_html=True)
                
                # Create pie chart
                fig, ax = plt.subplots()
                ax.pie(
                    [match_percentage, 100-match_percentage],
                    labels=['Matched Skills', 'Missing Skills'],
                    colors=['#4CAF50', '#F44336'],
                    autopct='%1.1f%%',
                    startangle=90,
                    wedgeprops={'linewidth': 1, 'edgecolor': 'white'}
                )
                ax.axis('equal')  # Equal aspect ratio ensures circular pie
                
                # Display chart in Streamlit
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.pyplot(fig)
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Course recommendations
                if recommendations:
                    st.subheader("📚 Recommended Courses")
                    for course in recommendations:
                        create_course_card(course)
                else:
                    st.info("🎉 You're already qualified! No additional courses needed.")
    else:
        st.error("Please enter a job title")

# Sidebar
with st.sidebar:
    st.markdown("## How It Works")
    st.markdown("""
    1. Enter a job title (e.g., "Data Scientist")
    2. List your current skills or upload your resume
    3. Get personalized course recommendations
    """)
    st.divider()
    st.markdown("🛠 Powered by:")
    st.markdown("- Python • Streamlit • Matplotlib")