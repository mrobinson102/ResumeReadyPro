prompt_templates = {
    "Internship & Co-op Experience": """
Generate a résumé section titled 'Internship & Co-op Experience'. Use the following input to format each role clearly with company name, role, dates, and bullet points for responsibilities and accomplishments. Highlight technologies used and any metrics if mentioned.

Input:
{user_input}

Format output in markdown or plain text suitable for a professional resume.
""",
    "Categorized Project Sections": """
You are helping a user build a résumé. Categorize the following projects into three sections:

1. Internship Projects
2. Academic Coursework Projects
3. Personal Side Projects

For each project, include:
- Project title
- Role or responsibility
- Technologies used (languages, frameworks)
- Key accomplishment or what was built

Input:
{user_input}

Return output in resume bullet style under each category.
""",
    "GitHub Repo to Bullet Points": """
For each of the following GitHub repositories, generate a résumé-ready bullet point that describes:
- What the project does
- Technologies used
- A notable feature or result
- Keep each bullet under 30 words

GitHub Repo List:
{user_input}

Output each bullet with a hyperlink to the repo.
""",
    "Tech Resume Summary (Amazon/Microsoft Style)": """
Write a compelling 2–3 sentence professional summary for a résumé targeting top tech companies (e.g., Microsoft, Amazon). The tone should be confident, clear, and metrics-driven.

Use the input below. Highlight relevant languages, platforms, and impact.

Input:
{user_input}
"""
}
 
