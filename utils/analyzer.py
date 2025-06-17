import re
import requests
import json
import os
from dotenv import load_dotenv

def extract_text(file):
    text = ""

    if file.type == "application/pdf":
        import pdfplumber
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    elif file.type == "text/plain":
        text = file.read().decode("utf-8")

    return text.lower()


def analyze_text(text, file_type="pdf"):
    # Check for blank or empty text
    if not text or text.isspace():
        return 0, ["❌ Error: The file appears to be blank or empty. Please upload a valid resume."], {"Error": 0}, []

    feedback = []
    total_score = 0
    breakdown = {}
    suggestions = []

    # ---------- 1. Skills (25 points) ----------
    technical_skills = {
        "Programming": ["python", "java", "c++", "javascript", "typescript", "ruby", "php", "swift", "kotlin", "go", "rust"],
        "Web": ["html", "css", "react", "angular", "vue", "node.js", "django", "flask", "spring", "express"],
        "Data": ["sql", "mysql", "postgresql", "mongodb", "nosql", "data analysis", "data science", "machine learning", "ai", "tensorflow", "pytorch"],
        "DevOps": ["docker", "kubernetes", "aws", "azure", "gcp", "ci/cd", "jenkins", "git", "linux"],
        "Tools": ["jira", "agile", "scrum", "excel", "power bi", "tableau"]
    }
    
    found_skills = set()
    missing_categories = []
    for category, skills in technical_skills.items():
        category_skills = [skill for skill in skills if skill in text]
        found_skills.update(category_skills)
        if len(category_skills) < 2:  # If less than 2 skills found in a category
            missing_categories.append(category)
    
    skill_score = min(25, int((len(found_skills) / 10) * 25))
    total_score += skill_score
    breakdown["Technical Skills"] = skill_score

    if found_skills:
        feedback.append(f"✅ Technical Skills found: {', '.join(sorted(found_skills))} ({skill_score}/25)")
        if missing_categories:
            suggestions.append(f"💡 Consider adding more skills in these areas: {', '.join(missing_categories)}")
    else:
        feedback.append(f"❌ No technical skills found ({skill_score}/25)")
        suggestions.append("💡 Add a dedicated 'Technical Skills' section with relevant programming languages, tools, and technologies")

    # ---------- 2. Resume Sections (20 points) ----------
    section_patterns = {
        "education": r"(?i)(?:^|\n)\s*(?:education|academic|qualification|degree|university|college|bachelor|master|phd|b\.?s\.?|m\.?s\.?|b\.?e\.?|m\.?e\.?|b\.?tech|m\.?tech)[\s:]*",
        "experience": r"(?i)(?:^|\n)\s*(?:experience|work history|employment|professional experience|work experience|job history|career|professional background|work background)[\s:]*",
        "projects": r"(?i)(?:^|\n)\s*(?:projects|portfolio|work samples|case studies|project experience|project work|project history|project portfolio|project showcase)[\s:]*",
        "skills": r"(?i)(?:^|\n)\s*(?:skills|technical skills|competencies|expertise|technical expertise|core competencies|key skills|technical competencies|skill set|areas of expertise)[\s:]*",
        "certifications": r"(?i)(?:^|\n)\s*(?:certifications|certificates|accreditations|professional certifications|technical certifications|industry certifications|certified|accredited)[\s:]*",
        "summary": r"(?i)(?:^|\n)\s*(?:summary|profile|objective|about me|career summary|professional summary|executive summary|career objective|professional profile)[\s:]*",
        "achievements": r"(?i)(?:^|\n)\s*(?:achievements|accomplishments|awards|recognition|honors|distinctions|merits|successes|milestones|key achievements)[\s:]*"
    }

    found_sections = []
    for section, pattern in section_patterns.items():
        if re.search(pattern, text):
            found_sections.append(section)
        elif section == "skills":
            skill_count = sum(1 for skill in ["python", "java", "javascript", "html", "css", "sql", "react", "angular", "node", "aws"] if skill in text)
            if skill_count >= 3:
                found_sections.append(section)
        elif section == "education":
            education_indicators = ["bachelor", "master", "phd", "b.s.", "m.s.", "b.e.", "m.e.", "b.tech", "m.tech", "university", "college"]
            if any(indicator in text for indicator in education_indicators):
                found_sections.append(section)

    section_score = int((len(found_sections) / len(section_patterns)) * 20)
    total_score += section_score
    breakdown["Resume Sections"] = section_score

    if section_score == 20:
        feedback.append(f"✅ All essential sections found ({section_score}/20)")
    else:
        missing_sections = set(section_patterns.keys()) - set(found_sections)
        feedback.append(f"⚠️ Found {len(found_sections)}/7 sections ({section_score}/20)")
        if missing_sections:
            feedback.append(f"❌ Missing sections: {', '.join(missing_sections)}")
            suggestions.append(f"💡 Add these missing sections: {', '.join(missing_sections)}")

    # ---------- 3. Contact & Professional Links (15 points) ----------
    contact_patterns = {
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "phone": r"(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
        "github": r"github\.com/[a-zA-Z0-9-]+",
        "linkedin": r"linkedin\.com/in/[a-zA-Z0-9-]+",
        "portfolio": r"(?:portfolio|website|personal site)[:\s]+(?:https?://)?[^\s]+"
    }

    contact_score = 0
    missing_contact = []
    for item, pattern in contact_patterns.items():
        if re.search(pattern, text):
            contact_score += 3
        else:
            missing_contact.append(item)

    total_score += contact_score
    breakdown["Contact Info"] = contact_score

    if contact_score == 15:
        feedback.append(f"✅ Complete contact information found ({contact_score}/15)")
    else:
        feedback.append(f"⚠️ Contact information partially complete ({contact_score}/15)")
        if missing_contact:
            suggestions.append(f"💡 Add your {', '.join(missing_contact)} to make it easier for recruiters to contact you")

    # ---------- 4. Action Words & Impact (20 points) ----------
    action_words = {
        "Leadership": ["led", "managed", "directed", "supervised", "coordinated", "mentored"],
        "Achievement": ["achieved", "increased", "improved", "optimized", "enhanced", "reduced"],
        "Technical": ["developed", "implemented", "designed", "architected", "engineered", "programmed"],
        "Business": ["generated", "saved", "reduced", "increased", "streamlined", "automated"]
    }

    action_score = 0
    used_actions = set()
    missing_action_categories = []
    for category, words in action_words.items():
        category_actions = [word for word in words if word in text]
        used_actions.update(category_actions)
        action_score += len(category_actions) * 1.25
        if len(category_actions) < 2:
            missing_action_categories.append(category)

    action_score = min(20, action_score)
    total_score += action_score
    breakdown["Action Words"] = action_score

    if used_actions:
        feedback.append(f"✅ Strong action words used: {', '.join(sorted(used_actions))} ({action_score}/20)")
        if missing_action_categories:
            suggestions.append(f"💡 Add more {', '.join(missing_action_categories)} action words to strengthen your achievements")
    else:
        feedback.append(f"❌ Limited use of action words ({action_score}/20)")
        suggestions.append("💡 Use more action verbs to describe your achievements and responsibilities")

    # ---------- 5. Quantified Results (20 points) ----------
    number_patterns = [
        r"\d+(?:\.\d+)?%",  # Percentages
        r"\$\d+(?:,\d+)*(?:\.\d+)?",  # Dollar amounts
        r"\d+(?:,\d+)*(?:\.\d+)?\s*(?:users|customers|clients|employees)",  # User metrics
        r"\d+(?:,\d+)*(?:\.\d+)?\s*(?:increase|decrease|reduction|growth)",  # Growth metrics
        r"\d+(?:,\d+)*(?:\.\d+)?\s*(?:days|weeks|months|years)",  # Time metrics
    ]

    quantified_results = []
    for pattern in number_patterns:
        matches = re.finditer(pattern, text)
        for match in matches:
            context = text[max(0, match.start()-50):min(len(text), match.end()+50)]
            quantified_results.append(context.strip())

    quantity_score = min(20, len(quantified_results) * 4)
    total_score += quantity_score
    breakdown["Quantified Results"] = quantity_score

    if quantified_results:
        feedback.append(f"✅ Found {len(quantified_results)} quantified results ({quantity_score}/20)")
    else:
        feedback.append(f"❌ No quantified results found ({quantity_score}/20)")
        suggestions.append("💡 Add specific numbers and metrics to quantify your achievements (e.g., 'increased efficiency by 25%', 'managed team of 10 developers')")

    # Add overall suggestions based on total score
    if total_score < 60:
        suggestions.append("💡 Consider a complete resume overhaul focusing on adding missing sections and quantifying achievements")
    elif total_score < 80:
        suggestions.append("💡 Your resume is good but could be improved by adding more quantified results and technical skills")
    else:
        suggestions.append("💡 Great resume! Consider adding more industry-specific keywords to improve ATS matching")

    # ---------- Return ----------
    return total_score, feedback, breakdown, suggestions