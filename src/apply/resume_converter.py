"""
Converts the tailored plain-text resume into a PDF file
that can be uploaded to job application portals.
Requires: pip install reportlab
"""

from pathlib import Path


def text_to_pdf(text: str, output_path: str) -> str:
    """Convert resume text to a clean PDF. Returns the output path."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.enums import TA_LEFT

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=0.75 * inch,
            rightMargin=0.75 * inch,
            topMargin=0.75 * inch,
            bottomMargin=0.75 * inch,
        )
        styles = getSampleStyleSheet()
        name_style = ParagraphStyle("name", fontSize=14, fontName="Helvetica-Bold", spaceAfter=4)
        header_style = ParagraphStyle("hdr", fontSize=10, fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=2)
        body_style = ParagraphStyle("body", fontSize=9, fontName="Helvetica", spaceAfter=2, leading=13)

        story = []
        lines = text.strip().split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                story.append(Spacer(1, 4))
                continue
            if i == 0:
                story.append(Paragraph(line, name_style))
            elif line.isupper() or (line.endswith(":") and len(line) < 40):
                story.append(Paragraph(line, header_style))
            elif line.startswith("•") or line.startswith("-"):
                story.append(Paragraph(f"&nbsp;&nbsp;{line}", body_style))
            else:
                story.append(Paragraph(line, body_style))

        doc.build(story)
        return output_path

    except ImportError:
        # Fallback: write as .txt with .pdf extension (some ATS accept this)
        Path(output_path.replace(".pdf", ".txt")).write_text(text)
        return output_path.replace(".pdf", ".txt")


def prepare_resume_file(tailored_text: str, company: str, output_dir: str = "resumes") -> str:
    """Save a tailored resume as PDF. Returns file path."""
    Path(output_dir).mkdir(exist_ok=True)
    safe_name = company.lower().replace(" ", "_").replace("/", "_")[:30]
    path = f"{output_dir}/Dhwani_Soni_Resume_{safe_name}.pdf"
    return text_to_pdf(tailored_text, path)
