import os
import io
import html
import re
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect

class VersionReportCanvas(canvas.Canvas):
    """Two-pass canvas for professional headers and footers with total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, num_pages):
        self.saveState()
        w, h = self._pagesize
        
        # Header on pages > 1
        if self._pageNumber > 1:
            self.setFont('Helvetica-Bold', 8)
            self.setFillColor(colors.HexColor('#475569'))
            self.drawString(45, h - 35, "PLAGIARISM ANALYZER — VERSION SIMILARITY AUDIT REPORT")
            self.setFont('Helvetica', 8)
            self.drawRightString(w - 45, h - 35, "Confidential Version Control Verification")
            
            self.setStrokeColor(colors.HexColor('#cbd5e1'))
            self.setLineWidth(0.5)
            self.line(45, h - 40, w - 45, h - 40)

        # Footer on ALL pages
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(45, 30, "CONFIDENTIAL & USER-SPECIFIC — Plagiarism Analyzer Version Control Engine")
        self.drawRightString(w - 45, 30, f"Page {self._pageNumber} of {num_pages}")
        
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.5)
        self.line(45, 42, w - 45, 42)
        
        self.restoreState()

def safe_p(text, style):
    if not text:
        return Paragraph("-", style)
    escaped = html.escape(str(text))
    return Paragraph(escaped, style)

class VersionReportGenerator:
    """
    Dedicated generator for Version Similarity Analysis PDF reports.
    Completely isolated from single and multi report generators.
    """

    def generate_report(self, group_name, v1_info, v2_info, comparison_data, user_name="Authenticated User", report_id=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=45,
            rightMargin=45,
            topMargin=50,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()
        
        # Custom typography styles
        styles.add(ParagraphStyle(
            'VC_MainTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=20,
            leading=24,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            'VC_SubTitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=colors.HexColor('#475569'),
            spaceAfter=15
        ))
        styles.add(ParagraphStyle(
            'VC_SectionHead',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=12,
            spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            'VC_MetaLabel',
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#475569')
        ))
        styles.add(ParagraphStyle(
            'VC_MetaVal',
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#0f172a')
        ))
        styles.add(ParagraphStyle(
            'VC_TableCell',
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        ))
        styles.add(ParagraphStyle(
            'VC_TableHead',
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#334155')
        ))
        styles.add(ParagraphStyle(
            'VC_BadgeUnchanged',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#059669')
        ))
        styles.add(ParagraphStyle(
            'VC_BadgeModified',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#d97706')
        ))
        styles.add(ParagraphStyle(
            'VC_BadgeAdded',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#2563eb')
        ))
        styles.add(ParagraphStyle(
            'VC_BadgeRemoved',
            fontName='Helvetica-Bold',
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor('#dc2626')
        ))

        story = []

        # 1. Title Banner
        story.append(Paragraph("PLAGIARISM ANALYZER", ParagraphStyle('TopPre', fontName='Helvetica-Bold', fontSize=9, textColor=colors.HexColor('#6366f1'), spaceAfter=2)))
        story.append(Paragraph("VERSION SIMILARITY ANALYSIS REPORT", styles['VC_MainTitle']))
        story.append(Paragraph("Automated Cross-Version Diff Analysis & Textual Evolution Audit", styles['VC_SubTitle']))

        # Divider bar
        d = Drawing(505, 3)
        d.add(Rect(0, 0, 505, 2, fillColor=colors.HexColor('#6366f1'), strokeColor=None))
        story.append(d)
        story.append(Spacer(1, 12))

        # 2. Metadata Grid
        rep_str = f"VC-{report_id}" if report_id else f"VC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        now_str = datetime.now().strftime("%d %B %Y, %I:%M %p")

        meta_data = [
            [
                Paragraph("Document Group:", styles['VC_MetaLabel']),
                Paragraph(html.escape(group_name), styles['VC_MetaVal']),
                Paragraph("Report Reference:", styles['VC_MetaLabel']),
                Paragraph(rep_str, styles['VC_MetaVal'])
            ],
            [
                Paragraph("Baseline Version:", styles['VC_MetaLabel']),
                Paragraph(f"Version {v1_info.get('version_number', 1)}: {html.escape(v1_info.get('filename', 'doc_v1'))}", styles['VC_MetaVal']),
                Paragraph("Timestamp:", styles['VC_MetaLabel']),
                Paragraph(now_str, styles['VC_MetaVal'])
            ],
            [
                Paragraph("Compared Version:", styles['VC_MetaLabel']),
                Paragraph(f"Version {v2_info.get('version_number', 2)}: {html.escape(v2_info.get('filename', 'doc_v2'))}", styles['VC_MetaVal']),
                Paragraph("Authorized User:", styles['VC_MetaLabel']),
                Paragraph(html.escape(user_name), styles['VC_MetaVal'])
            ]
        ]
        meta_table = Table(meta_data, colWidths=[105, 160, 105, 135])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#f1f5f9')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # 3. Dual Executive KPI Block
        ver_sim = comparison_data.get('version_similarity', 0.0)
        match_pct = comparison_data.get('matching_percentage', 0.0)
        
        sim_color = '#dc2626' if ver_sim >= 70 else ('#d97706' if ver_sim >= 40 else '#059669')
        match_color = '#dc2626' if match_pct >= 70 else ('#d97706' if match_pct >= 40 else '#059669')

        kpi_data = [
            [
                Paragraph("<font size=10 color='#475569'><b>VERSION SIMILARITY SCORE</b></font><br/><br/>"
                          f"<font size=24 color='{sim_color}'><b>{ver_sim:.1f}%</b></font><br/><br/>"
                          "<font size=7.5 color='#64748b'>Macro-level semantic & structural closeness across versions</font>",
                          ParagraphStyle('KPI1', fontName='Helvetica', alignment=1)),
                Paragraph("<font size=10 color='#475569'><b>CONTENT MATCH / PLAGIARISM</b></font><br/><br/>"
                          f"<font size=24 color='{match_color}'><b>{match_pct:.1f}%</b></font><br/><br/>"
                          "<font size=7.5 color='#64748b'>Micro-level verbatim and substantial copying ratio against base version</font>",
                          ParagraphStyle('KPI2', fontName='Helvetica', alignment=1))
            ]
        ]
        kpi_table = Table(kpi_data, colWidths=[250, 255])
        kpi_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#f8fafc')),
            ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#f8fafc')),
            ('BOX', (0, 0), (0, 0), 1, colors.HexColor('#cbd5e1')),
            ('BOX', (1, 0), (1, 0), 1, colors.HexColor('#cbd5e1')),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ]))
        story.append(kpi_table)
        story.append(Spacer(1, 14))

        # 4. Content Change Statistics Table
        stats = comparison_data.get('statistics', {})
        story.append(Paragraph("Content Evolution Statistics", styles['VC_SectionHead']))
        
        stat_rows = [
            [
                Paragraph("<b>Metric Category</b>", styles['VC_TableHead']),
                Paragraph("<b>Sentence Count</b>", styles['VC_TableHead']),
                Paragraph("<b>Proportion (%)</b>", styles['VC_TableHead']),
                Paragraph("<b>Evolution Status</b>", styles['VC_TableHead'])
            ],
            [
                Paragraph("Unchanged Content", styles['VC_TableCell']),
                Paragraph(str(stats.get('unchanged_count', 0)), styles['VC_TableCell']),
                Paragraph(f"{stats.get('unchanged_pct', 0.0):.1f}%", styles['VC_TableCell']),
                Paragraph("Retained without substantial modification", styles['VC_TableCell'])
            ],
            [
                Paragraph("Modified / Paraphrased", styles['VC_TableCell']),
                Paragraph(str(stats.get('modified_count', 0)), styles['VC_TableCell']),
                Paragraph(f"{stats.get('modified_pct', 0.0):.1f}%", styles['VC_TableCell']),
                Paragraph("Altered, expanded, or contextually reworded", styles['VC_TableCell'])
            ],
            [
                Paragraph("Newly Added Content", styles['VC_TableCell']),
                Paragraph(str(stats.get('added_count', 0)), styles['VC_TableCell']),
                Paragraph(f"{stats.get('added_pct', 0.0):.1f}%", styles['VC_TableCell']),
                Paragraph("Unique additions present only in newer version", styles['VC_TableCell'])
            ],
            [
                Paragraph("Removed Content", styles['VC_TableCell']),
                Paragraph(str(stats.get('removed_count', 0)), styles['VC_TableCell']),
                Paragraph(f"{stats.get('removed_pct', 0.0):.1f}%", styles['VC_TableCell']),
                Paragraph("Existed in baseline version, omitted in revision", styles['VC_TableCell'])
            ]
        ]
        stat_table = Table(stat_rows, colWidths=[130, 85, 95, 195])
        stat_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(stat_table)
        story.append(Spacer(1, 14))

        # 5. Detailed Sentence Alignment Table
        detailed = comparison_data.get('detailed_comparison', [])
        story.append(Paragraph(f"Detailed Sentence-Level Audit ({len(detailed)} Items)", styles['VC_SectionHead']))

        diff_rows = [
            [
                Paragraph("<b>#</b>", styles['VC_TableHead']),
                Paragraph("<b>Status</b>", styles['VC_TableHead']),
                Paragraph("<b>Sim %</b>", styles['VC_TableHead']),
                Paragraph("<b>Version 1 (Baseline Excerpt)</b>", styles['VC_TableHead']),
                Paragraph("<b>Version 2 (Revision Excerpt)</b>", styles['VC_TableHead'])
            ]
        ]

        for item in detailed[:75]: # Cap at 75 to keep PDF fast & readable
            st = item.get('status', 'MODIFIED')
            if st == 'UNCHANGED':
                badge = Paragraph(f"<b>UNCHANGED</b>", styles['VC_BadgeUnchanged'])
                bg_color = colors.HexColor('#f0fdf4')
            elif st == 'MODIFIED':
                badge = Paragraph(f"<b>MODIFIED</b>", styles['VC_BadgeModified'])
                bg_color = colors.HexColor('#fffbeb')
            elif st == 'ADDED':
                badge = Paragraph(f"<b>ADDED</b>", styles['VC_BadgeAdded'])
                bg_color = colors.HexColor('#eff6ff')
            else:
                badge = Paragraph(f"<b>REMOVED</b>", styles['VC_BadgeRemoved'])
                bg_color = colors.HexColor('#fef2f2')

            sim_val = f"{item.get('similarity', 0.0):.1f}%" if st in ['UNCHANGED', 'MODIFIED'] else "-"

            diff_rows.append([
                Paragraph(str(item.get('id', '')), styles['VC_TableCell']),
                badge,
                Paragraph(sim_val, styles['VC_TableCell']),
                safe_p(item.get('v1_text', '-'), styles['VC_TableCell']),
                safe_p(item.get('v2_text', '-'), styles['VC_TableCell'])
            ])

        diff_table = Table(diff_rows, colWidths=[20, 65, 40, 190, 190])
        diff_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e2e8f0')),
            ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(diff_table)

        # 6. Conclusion
        story.append(Spacer(1, 14))
        conclusion_text = (
            f"<b>Audit Summary & Conclusion:</b> Comparison between {html.escape(v1_info.get('filename', 'V1'))} and "
            f"{html.escape(v2_info.get('filename', 'V2'))} revealed an overall Version Similarity score of <b>{ver_sim:.1f}%</b> "
            f"with a direct Content Matching ratio of <b>{match_pct:.1f}%</b>. "
            f"The revised document contains {stats.get('unchanged_count', 0)} unchanged sentences, "
            f"{stats.get('modified_count', 0)} modified segments, and {stats.get('added_count', 0)} new additions. "
            "This report is generated securely for the authorized owner's private version history."
        )
        story.append(Paragraph(conclusion_text, styles['VC_MetaVal']))

        # Build PDF
        doc.build(story, canvasmaker=VersionReportCanvas)
        buffer.seek(0)
        return buffer
