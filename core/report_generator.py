from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import io

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#4f46e5'),
            alignment=0,
            spaceAfter=20
        )
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#111827'),
            spaceAfter=12
        )
        self.normal_style = self.styles['Normal']
        self.small_style = ParagraphStyle('SmallStyle', parent=self.styles['Normal'], fontSize=8, textColor=colors.grey)

    def _get_header(self, doc_type="Single Analysis"):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            Paragraph("Plagiarism Analyzer Report", self.title_style),
            Paragraph(f"Type: {doc_type}", self.normal_style),
            Paragraph(f"Generated on: {now}", self.small_style),
            Spacer(1, 24)
        ]

    def _sanitize_text(self, text):
        # Remove hard newlines that fragment words, but keep paragraph breaks
        # Split by double newline to preserve paragraph structure
        paragraphs = text.split('\n\n')
        sanitized_paragraphs = []
        for p in paragraphs:
            # For each paragraph, replace single newlines with a space
            clean_p = ' '.join(p.split('\n'))
            sanitized_paragraphs.append(clean_p)
        return '<br/><br/>'.join(sanitized_paragraphs)

    def generate_single_report(self, text, results):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50)
        elements = self._get_header("Single Document Analysis")

        # Overall Score
        elements.append(Paragraph("Overall Findings", self.header_style))
        score = results.get('overall_percentage', 0)
        score_html = f"<font size='14' color='#4f46e5'><b>Plagiarism Score: {score:.1f}%</b></font>"
        elements.append(Paragraph(score_html, self.normal_style))
        elements.append(Spacer(1, 15))

        # Top Matches Table
        matches = results.get('top_matches', [])
        if matches:
            elements.append(Paragraph("Top Overlap Sources", self.styles['Heading4']))
            data = [["Source Content Preview", "Match %"]]
            for m in matches:
                data.append([Paragraph(m['title'], self.normal_style), f"{(m['score']*100):.1f}%"])
            
            t = Table(data, colWidths=[420, 80])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f3f4f6')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#374151')),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 10),
                ('TOPPADDING', (0,0), (-1,0), 10),
                ('LEFTPADDING', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d1d5db'))
            ]))
            elements.append(t)
            elements.append(Spacer(1, 25))

        # Original Text
        elements.append(Paragraph("Analyzed Document Content", self.header_style))
        sanitized_content = self._sanitize_text(text)
        elements.append(Paragraph(sanitized_content, self.normal_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_multi_report(self, doc_names, matrix, pairwise_results):
        buffer = io.BytesIO()
        # Use a wider horizontal margin for matrix
        doc = SimpleDocTemplate(buffer, pagesize=letter, leftMargin=30, rightMargin=30, topMargin=50, bottomMargin=50)
        elements = self._get_header("Multi-Document Cross-Comparison")

        # Summary Checklist
        elements.append(Paragraph("Documents Analyzed", self.header_style))
        for i, name in enumerate(doc_names):
            elements.append(Paragraph(f"• {name}", self.normal_style))
        elements.append(Spacer(1, 20))

        # Similarity Matrix
        elements.append(Paragraph("Inter-Similarity Matrix (Pairwise Overlap)", self.header_style))
        
        # Matrix Table
        data = [["File name"] + doc_names]
        for name1 in doc_names:
            row = [Paragraph(name1, self.normal_style)]
            for name2 in doc_names:
                score = matrix[name1][name2]
                row.append(f"{score:.1f}%")
            data.append(row)
        
        # Professional column width formula
        total_avail_width = 540
        file_col_width = 100
        other_col_width = (total_avail_width - file_col_width) / len(doc_names)
        col_widths = [file_col_width] + [other_col_width] * len(doc_names)

        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
            ('FONTSIZE', (0,0), (-1,-1), 7),
            ('BACKGROUND', (0,1), (0,-1), colors.HexColor('#f9fafb')),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 40))

        # Pairwise details
        critical_pairs = [p for p in pairwise_results if p['similarity_percentage'] > 5]
        if critical_pairs:
            elements.append(Paragraph("Detailed Pairwise Summaries", self.header_style))
            for pair in critical_pairs:
                elements.append(Paragraph(f"<b><u>{pair['doc1']}</u> vs <u>{pair['doc2']}</u></b>", self.normal_style))
                elements.append(Paragraph(f"Similarity Score: <b>{pair['similarity_percentage']:.1f}%</b>", self.normal_style))
                elements.append(Paragraph(f"Significant matches identified: {pair['matching_sentences_count']} similar segments.", self.small_style))
                elements.append(Spacer(1, 12))

        doc.build(elements)
        buffer.seek(0)
        return buffer
