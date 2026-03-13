def mode_form_basic(data):
    # Process structured fields
    structured_data = {
        "name": data.get("name", ""),
        "mobile_number": data.get("mobile_number", ""),
        "mail_id": data.get("mail_id", ""),
        "linkedin_link": data.get("linkedin_link", ""),
        "github_link": data.get("github_link", ""),
        "portfolio_link": data.get("portfolio_link", ""),
        "summary": data.get("summary", ""),
        "skills": data.get("skills", []),
        "companies": data.get("companies", []),
        "projects": data.get("projects", []),
        "educations": data.get("educations", []),
        "certificates": data.get("certificates", [])
    }

    # Format companies/projects details as lists if they are strings
    for company in structured_data["companies"]:
        if isinstance(company.get("experience"), str):
            company["experience"] = [line.strip("- ").strip() for line in company["experience"].split("\n") if line.strip()]

    for project in structured_data["projects"]:
        if isinstance(project.get("project_details"), str):
            project["project_details"] = [line.strip("- ").strip() for line in project["project_details"].split("\n") if line.strip()]

    return structured_data