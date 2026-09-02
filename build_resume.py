#!/usr/bin/env python3
"""
Generate compact ATS resume outputs from resume.yaml.

Usage:
  python build_resume.py --pdf
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    raise SystemExit("Install PyYAML: pip install pyyaml")

ROOT = Path(__file__).parent
YAML_PATH = ROOT / "resume.yaml"
MD_PATH = ROOT / "resume.md"
HTML_PATH = ROOT / "resume.html"
PDF_PATH = ROOT / "resume.pdf"

ACCENT = "#0f4c75"
TEXT = "#1a1a1a"
MUTED = "#4a5568"


def format_date_range(start: str, end: str) -> str:
    months = {
        "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr",
        "05": "May", "06": "Jun", "07": "Jul", "08": "Aug",
        "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec",
    }

    def fmt(value: str) -> str:
        if value == "present":
            return "Present"
        if len(value) == 4:
            return value
        if len(value) == 7 and value[4] == "-":
            y, m = value.split("-")
            return f"{months.get(m, m)} {y}"
        return value

    return f"{fmt(start)} – {fmt(end)}"


def skill_lines(skills: dict) -> list[str]:
    labels = {
        "core": "Core",
        "supporting": "Also skilled in",
        "domains": "Domain experience",
    }
    lines = []
    for key, label in labels.items():
        items = skills.get(key, [])
        if items:
            lines.append(f"**{label}:** {', '.join(items)}")
    return lines


def trim_bullets(job: dict, max_bullets: int) -> list[str]:
    return job.get("highlights", [])[:max_bullets]


def featured_projects(data: dict) -> list[dict]:
    limit = data.get("meta", {}).get("max_featured_projects", 3)
    projects = [p for p in data.get("projects", []) if p.get("featured", True)]
    return projects[:limit]


def build_markdown(data: dict) -> str:
    p = data["personal"]
    meta = data.get("meta", {})
    max_bullets = meta.get("max_bullets_per_role", 3)
    show_job_tech = meta.get("show_job_technologies", False)

    lines = [
        f"# {p['full_name']}",
        "",
        f"**{p['professional_title']}**",
        "",
        f"{p['location']} | {p['email']} | {p['phone']}  ",
        f"LinkedIn: {p['linkedin'].replace('https://', '')} | Portfolio: {p['portfolio'].replace('https://', '')}",
        "",
        "## Summary",
        "",
        data["summary"].strip(),
        "",
        "## Skills",
        "",
    ]
    lines.extend(skill_lines(data["skills"]))
    lines.extend(["", "## Experience", ""])

    for job in data["experience"]:
        lines.extend([
            f"### {job['title']} — {job['company']}",
            f"{format_date_range(job['start_date'], job['end_date'])} | {job['location']}",
            "",
        ])
        for bullet in trim_bullets(job, max_bullets):
            lines.append(f"- {bullet}")
        if show_job_tech and job.get("technologies"):
            lines.append(f"- *Stack: {', '.join(job['technologies'])}*")
        lines.append("")

    lines.extend(["## Key Projects", ""])
    for project in featured_projects(data):
        tech = ", ".join(project["technologies"][:5])
        lines.append(
            f"- **{project['name']}** — {project['description'].strip()} ({tech})"
        )

    edu = data["education"][0]
    cert = data["certifications"][0]["name"] if data.get("certifications") else ""
    lines.extend([
        "",
        "## Education",
        "",
        f"**{edu['degree']}**, {edu['institution']} ({edu['start_date']}–{edu['end_date']})",
        f"**Certification:** {cert}" if cert else "",
        "",
    ])
    return "\n".join(line for line in lines if line is not None)


def build_html(data: dict) -> str:
    p = data["personal"]
    meta = data.get("meta", {})
    max_bullets = meta.get("max_bullets_per_role", 3)
    esc = html.escape

    skills_html = "\n".join(
        f'    <div class="skill-row"><span class="skill-label">{esc(line.split(":**")[0].replace("**", ""))}</span> '
        f'<span class="skill-items">{esc(line.split(":**", 1)[1].strip())}</span></div>'
        for line in skill_lines(data["skills"])
    )

    exp_html = []
    for job in data["experience"]:
        bullets = "\n".join(
            f"        <li>{esc(b)}</li>" for b in trim_bullets(job, max_bullets)
        )
        exp_html.append(f"""
    <article class="entry">
      <div class="entry-head">
        <div>
          <h3>{esc(job['title'])}</h3>
          <p class="company">{esc(job['company'])} · {esc(job['location'])}</p>
        </div>
        <span class="dates">{esc(format_date_range(job['start_date'], job['end_date']))}</span>
      </div>
      <ul>{bullets}
      </ul>
    </article>""")

    projects_html = "\n".join(
        f"""    <div class="project">
      <span class="project-name">{esc(project['name'])}</span>
      <span class="project-desc">— {esc(project['description'].strip())}</span>
      <span class="project-tech">{esc(', '.join(project['technologies'][:5]))}</span>
    </div>"""
        for project in featured_projects(data)
    )

    edu = data["education"][0]
    cert = data["certifications"][0]["name"] if data.get("certifications") else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{esc(p['full_name'])} — Resume</title>
  <style>
    @page {{ margin: 0.42in 0.48in; }}
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{
      font-family: Calibri, "Segoe UI", Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.32;
      color: {TEXT};
      max-width: 8.5in;
      margin: 0 auto;
      padding: 0.42in 0.48in;
      background: #fff;
    }}
    header {{
      border-bottom: 2.5px solid {ACCENT};
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}
    h1 {{
      font-size: 22pt;
      font-weight: 700;
      letter-spacing: -0.3px;
      color: {ACCENT};
      line-height: 1.1;
    }}
    .title {{
      font-size: 11.5pt;
      font-weight: 600;
      color: {MUTED};
      margin-top: 2px;
    }}
    .contact {{
      margin-top: 8px;
      font-size: 9.5pt;
      color: {MUTED};
    }}
    .contact a {{ color: {ACCENT}; text-decoration: none; }}
    h2 {{
      font-size: 10pt;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.8px;
      color: {ACCENT};
      border-bottom: 1px solid #d1dbe5;
      margin: 11px 0 7px;
      padding-bottom: 3px;
    }}
    .summary {{ font-size: 10.5pt; color: {TEXT}; }}
    .skill-row {{
      display: block;
      margin-bottom: 3px;
      font-size: 10pt;
    }}
    .skill-label {{
      font-weight: 700;
      color: {ACCENT};
      margin-right: 6px;
    }}
    .skill-items {{ color: {TEXT}; }}
    .entry {{ margin-bottom: 8px; }}
    .entry-head {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 12px;
    }}
    .entry h3 {{
      font-size: 10.8pt;
      font-weight: 700;
      color: {TEXT};
    }}
    .company {{
      font-size: 9.8pt;
      color: {MUTED};
      margin-top: 1px;
    }}
    .dates {{
      font-size: 9.5pt;
      font-weight: 600;
      color: {MUTED};
      white-space: nowrap;
    }}
    ul {{
      margin: 4px 0 0 16px;
      padding: 0;
    }}
    li {{
      margin-bottom: 2px;
      font-size: 10.2pt;
    }}
    .project {{
      margin-bottom: 5px;
      font-size: 10.2pt;
    }}
    .project-name {{ font-weight: 700; color: {TEXT}; }}
    .project-desc {{ color: {TEXT}; }}
    .project-tech {{
      display: block;
      font-size: 9.5pt;
      color: {MUTED};
      margin-top: 1px;
    }}
    .footer {{
      margin-top: 6px;
      font-size: 10pt;
      color: {TEXT};
    }}
    .footer strong {{ color: {ACCENT}; }}
    @media print {{
      body {{ padding: 0; }}
      .entry, .project {{ break-inside: avoid; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{esc(p['full_name'])}</h1>
    <p class="title">{esc(p['professional_title'])}</p>
    <p class="contact">
      {esc(p['location'])} ·
      <a href="mailto:{esc(p['email'])}">{esc(p['email'])}</a> ·
      {esc(p['phone'])} ·
      <a href="{esc(p['linkedin'])}">{esc(p['linkedin'].replace('https://', ''))}</a> ·
      <a href="{esc(p['portfolio'])}">{esc(p['portfolio'].replace('https://', ''))}</a>
    </p>
  </header>

  <h2>Summary</h2>
  <p class="summary">{esc(data['summary'].strip())}</p>

  <h2>Skills</h2>
  <section class="skills">
{skills_html}
  </section>

  <h2>Experience</h2>
  <section>
{''.join(exp_html)}
  </section>

  <h2>Key Projects</h2>
  <section>
{projects_html}
  </section>

  <h2>Education</h2>
  <p class="footer">
    <strong>{esc(edu['degree'])}</strong>, {esc(edu['institution'])} ({esc(edu['start_date'])}–{esc(edu['end_date'])})
    &nbsp;|&nbsp; <strong>Certification:</strong> {esc(cert)}
  </p>
</body>
</html>
"""


def find_browser() -> Path | None:
    candidates = [
        Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
        Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
        Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    ]
    for path in candidates:
        if path.exists():
            return path
    for name in ("msedge", "chrome", "google-chrome"):
        found = shutil.which(name)
        if found:
            return Path(found)
    return None


def generate_pdf() -> None:
    browser = find_browser()
    if not browser:
        raise SystemExit("PDF export failed: install Edge or Chrome.")

    html_uri = HTML_PATH.resolve().as_uri()
    if PDF_PATH.exists():
        PDF_PATH.unlink()

    subprocess.run(
        [
            str(browser),
            "--headless=new",
            "--disable-gpu",
            f"--print-to-pdf={PDF_PATH.resolve()}",
            "--no-pdf-header-footer",
            html_uri,
        ],
        check=True,
        capture_output=True,
    )
    print(f"Generated: {PDF_PATH}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build compact ATS resume")
    parser.add_argument("--pdf", action="store_true", help="Export resume.pdf")
    args = parser.parse_args()

    with YAML_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    MD_PATH.write_text(build_markdown(data), encoding="utf-8")
    HTML_PATH.write_text(build_html(data), encoding="utf-8")
    print(f"Generated: {MD_PATH}")
    print(f"Generated: {HTML_PATH}")

    if args.pdf:
        generate_pdf()


if __name__ == "__main__":
    main()
