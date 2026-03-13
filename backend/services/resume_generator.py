import tempfile
from flask import send_file
from docxtpl import DocxTemplate, RichText
import os


def create_link(doc, text, url):
    if not url:
        return ""
    
    # Clean and validate URL
    url_str = str(url).strip()
    if not url_str:
        return ""
    
    # Ensure scheme exists
    if not (url_str.startswith('http://') or url_str.startswith('https://') or url_str.startswith('mailto:')):
        url_str = 'https://' + url_str
        
    try:
        rt = RichText()
        # Add styled, clickable link
        rt.add(text, url_id=doc.build_url_id(url_str), color='0000FF', underline=True)
        return rt
    except Exception as e:
        print(f"Error creating link for {url_str}: {e}")
        return text


def generate_resume(data, user_id=None):
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(
        BASE_DIR,
        "../templates/resume_format.docx"
    )

    if not os.path.exists(template_path):
        template_path = os.path.join(BASE_DIR, "../templates/resume_template.docx")

    template = DocxTemplate(template_path)

    # Convert header links to clickable links
    if data.get("linkedin_link"):
        data["linkedin_link"] = create_link(template, "LinkedIn", data["linkedin_link"])
    if data.get("github_link"):
        data["github_link"] = create_link(template, "GitHub", data["github_link"])
    if data.get("portfolio_link"):
        data["portfolio_link"] = create_link(template, "Portfolio", data["portfolio_link"])
    if data.get("project_link"):
        data["project_link"] = create_link(template, "project_link", data["project_link"])

    # Normalize data and convert fields to RichText for template compatibility
    if "sections" not in data:
        sections = []

        # 1. SUMMARY
        if data.get("summary"):
            summary_rt = RichText()
            summary_rt.add(str(data["summary"]))
            sections.append({
                "title": "PROFESSIONAL SUMMARY",
                "content": summary_rt
            })

        # 2. SKILLS
        skills_str = ""
        for s in data.get("skills", []):
            main = str(s.get('main_skill', '')).strip()
            sub = str(s.get('sub_skills', '')).strip()
            if main:
                skills_str += f"{main}: {sub}\n"
            elif sub:
                skills_str += f"{sub}\n"

        if skills_str:
            sections.append({
                "title": "SKILLS",
                "content": skills_str.strip()
            })

        # 3. EXPERIENCE
        if data.get("companies"):
            exp_rt = RichText()
            for i, c in enumerate(data.get("companies", [])):
                if i > 0: exp_rt.add("\n")
                
                heading = f"{c.get('position','')} at {c.get('name','')}"
                dates = f" ({c.get('from','')} - {c.get('to','')})"
                exp_rt.add(heading, bold=True)
                exp_rt.add(dates + "\n")

                experience_lines = c.get("experience")
                if isinstance(experience_lines, list):
                    for bullet in experience_lines:
                        exp_rt.add(f"• {bullet}\n")
                elif experience_lines:
                    for line in str(experience_lines).split("\n"):
                        if line.strip():
                            exp_rt.add(f"• {line.strip()}\n")

            sections.append({
                "title": "EXPERIENCE",
                "content": exp_rt
            })

        # 4. PROJECTS
        if data.get("projects"):
            proj_rt = RichText()
            for i, p in enumerate(data.get("projects", [])):
                if i > 0: proj_rt.add("\n\n")
                
                title = str(p.get('title','')).strip()
                tools = str(p.get('tools_used','')).strip()
                link_url = str(p.get('project_link','')).strip()
                
                # Update individual project link in-place for templates using {{project.project_link}}
                if link_url:
                    p["project_link"] = create_link(template, "Link", link_url)
                
                proj_rt.add(title, bold=True)
                if tools:
                    proj_rt.add(f" | {tools}")
                
                if link_url:
                    proj_rt.add(" | ")
                    proj_rt.add(create_link(template, "Link", link_url))
                
                proj_rt.add("\n")
                
                details = p.get("project_details")
                if isinstance(details, list):
                    for bullet in details:
                        proj_rt.add(f"• {bullet}\n")
                elif details:
                    for line in str(details).split("\n"):
                        if line.strip():
                            proj_rt.add(f"• {line.strip()}\n")

            sections.append({
                "title": "PROJECTS",
                "content": proj_rt
            })

        # 5. EDUCATION
        if data.get("educations"):
            edu_str = ""
            for e in data.get("educations", []):
                edu_str += f"{e.get('field','')} {e.get('subject','')} from {e.get('college','')} ({e.get('college_from','')} - {e.get('college_to','')})\n"
            
            sections.append({
                "title": "EDUCATION",
                "content": edu_str.strip()
            })

        # 6. CERTIFICATIONS
        if data.get("certificates"):
            cert_str = ""
            for cert in data.get("certificates", []):
                cert_str += f"{cert.get('name','')} | {cert.get('issuer','')}\n"
            
            sections.append({
                "title": "CERTIFICATIONS",
                "content": cert_str.strip()
            })

        data["sections"] = sections

    # Render final template
    template.render(data)

    # Create user-specific directory
    storage_dir = os.path.join(
        BASE_DIR,
        "../temp_resumes",
        str(user_id) if user_id else "anonymous"
    )
    os.makedirs(storage_dir, exist_ok=True)

    name_slug = str(data.get('name') or 'output').replace(' ', '_')
    output_filename = f"resume_{name_slug}.docx"
    output_path = os.path.join(storage_dir, output_filename)

    template.save(output_path)
    return output_path