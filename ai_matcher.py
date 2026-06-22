# Simple AI Matcher - Works Every Time
import PyPDF2
import re

class ResumeJobMatcher:
    def __init__(self):
        pass
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + " "
            print(f"PDF extracted: {len(text)} chars")
        except Exception as e:
            print(f"PDF error: {e}")
        return text.lower()
    
    def clean_text(self, text):
        """Clean text"""
        return re.sub(r'[^a-z0-9\s]', ' ', text.lower())
    
    def calculate_match_score(self, resume_text, job_description):
        """Simple keyword matching"""
        if not resume_text or not job_description:
            return 0.0
        
        # Clean both texts
        resume = self.clean_text(resume_text)
        job = self.clean_text(job_description)
        
        # Get job keywords
        job_words = set(job.split())
        resume_words = set(resume.split())
        
        # Remove common words
        common = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'is', 'are', 'was', 'were'}
        job_words = job_words - common
        resume_words = resume_words - common
        
        # Calculate match
        if not job_words:
            return 50.0
        
        matched = len(job_words & resume_words)
        total = len(job_words)
        score = (matched / total) * 100
        
        print(f"Matched: {matched}/{total} = {score}%")
        return round(score, 1)
    
    def detailed_analysis(self, resume_text, job_description):
        """Detailed analysis"""
        
        print("\n" + "="*50)
        print("ANALYSIS STARTING")
        print(f"Resume: {len(resume_text)} chars")
        print(f"Job: {len(job_description)} chars")
        
        if len(resume_text) < 20:
            print("EMPTY RESUME!")
            return self._empty_result()
        
        # Get basic score
        overall = self.calculate_match_score(resume_text, job_description)
        
        # Tech skills
        tech_skills = [
            'python', 'django', 'flask', 'javascript', 'angular', 'react',
            'sql', 'postgresql', 'mysql', 'aws', 'docker', 'git',
            'api', 'rest', 'graphql', 'html', 'css', 'selenium'
        ]
        
        resume_lower = resume_text.lower()
        job_lower = job_description.lower()
        
        # Find matched skills
        matched = [s for s in tech_skills if s in resume_lower and s in job_lower]
        missing = [s for s in tech_skills if s in job_lower and s not in resume_lower]
        
        # Calculate scores
        skills_score = len(matched) / max(len([s for s in tech_skills if s in job_lower]), 1) * 100
        
        # Experience score
        exp_score = 70.0
        if '2017' in resume_text or '2018' in resume_text:
            exp_score = 80.0
        
        # Education score
        edu_score = 50.0
        if 'master' in resume_lower or 'm.s' in resume_lower:
            edu_score = 90.0
        elif 'bachelor' in resume_lower or 'b.s' in resume_lower:
            edu_score = 70.0
        
        # Keyword density
        job_words = set(self.clean_text(job_description).split())
        resume_words = set(self.clean_text(resume_text).split())
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at'}
        job_words = job_words - common_words
        
        keyword_density = len(job_words & resume_words) / max(len(job_words), 1) * 100
        
        # Strengths
        strengths = []
        if len(matched) >= 5:
            strengths.append(f"{len(matched)} key skills matched")
        if 'agile' in resume_lower:
            strengths.append("Agile experience")
        if any(str(year) in resume_text for year in range(2015, 2025)):
            strengths.append("Recent work experience")
        if 'master' in resume_lower:
            strengths.append("Advanced degree")
        
        if not strengths:
            strengths = ["Relevant experience"]
        
        # Suggestions
        suggestions = []
        if missing:
            suggestions.append(f"Add skills: {', '.join(missing[:3])}")
        if '%' not in resume_text:
            suggestions.append("Include quantifiable achievements")
        if overall < 60:
            suggestions.append("Add more job-relevant keywords")
        
        if not suggestions:
            suggestions = ["Resume looks good"]
        
        result = {
            'overall_score': round(overall, 1),
            'skills_score': round(skills_score, 1),
            'experience_score': round(exp_score, 1),
            'education_score': round(edu_score, 1),
            'keyword_density': round(keyword_density, 1),
            'matched_skills': matched[:8],
            'missing_skills': missing[:6],
            'strengths': strengths[:5],
            'suggestions': suggestions[:5]
        }
        
        print(f"RESULT: {overall}%")
        print("="*50 + "\n")
        
        return result
    
    def _empty_result(self):
        return {
            'overall_score': 0.0,
            'skills_score': 0.0,
            'experience_score': 0.0,
            'education_score': 0.0,
            'keyword_density': 0.0,
            'matched_skills': [],
            'missing_skills': ['No data'],
            'strengths': ['Upload valid PDF'],
            'suggestions': ['Try different PDF file']
        }


# Test
if __name__ == "__main__":
    print("Testing...")
    m = ResumeJobMatcher()
    
    resume = "python django flask postgresql angular javascript aws git"
    job = "python developer django postgresql angular experience"
    
    score = m.calculate_match_score(resume, job)
    print(f"Test score: {score}%")
    
    analysis = m.detailed_analysis(resume, job)
    print(f"Analysis: {analysis['overall_score']}%") 