from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from datetime import datetime
import io

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        # Custom styles for professional academic look
        self.title_style = ParagraphStyle(
            'TitleStyle',
            parent=self.styles['Heading1'],
            fontSize=22,
            textColor=colors.HexColor('#1e293b'),
            alignment=1, # Centered
            spaceAfter=25,
            fontName='Helvetica-Bold'
        )
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#4f46e5'),
            spaceBefore=15,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        self.sub_header_style = ParagraphStyle(
            'SubHeaderStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#334155'),
            fontName='Helvetica-Bold',
            spaceBefore=8,
            spaceAfter=5
        )
        self.normal_style = ParagraphStyle(
            'NormalStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            leading=14,
            alignment=0 # Left aligned
        )
        self.match_text_style = ParagraphStyle(
            'MatchTextStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            leading=12,
            leftIndent=20,
            textColor=colors.HexColor('#475569')
        )
        self.footer_style = ParagraphStyle(
            'FooterStyle',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=1
        )

    def _sanitize_text(self, text):
        if not text: return ""
        # Remove hard newlines, but keep double newlines for paragraph breaks
        text = text.replace('\r\n', '\n')
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        sanitized = []
        for p in paragraphs:
            # Join single lines into one paragraph stream
            clean_p = ' '.join(p.split('\n'))
            sanitized.append(clean_p)
        return '<br/><br/>'.join(sanitized)

    def _get_page_header(self, doc_type):
        now = datetime.now().strftime("%B %d, %Y | %H:%M")
        return [
            Paragraph("Plagiarism Analysis Report", self.title_style),
            Paragraph(f"<b>Mode:</b> {doc_type}", self.normal_style),
            Paragraph(f"<b>Generated:</b> {now}", self.normal_style),
            Spacer(1, 10),
            Paragraph("<hr color='#e2e8f0'/>", self.normal_style),
            Spacer(1, 20)
        ]

    def generate_single_report(self, text, results):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            leftMargin=60, rightMargin=60, topMargin=60, bottomMargin=60
        )
        elements = self._get_page_header("Single Document Analysis")

        # Summary Section
        score = results.get('overall_percentage', 0)
        elements.append(Paragraph("Analysis Summary", self.header_style))
        summary_data = [
            ["Metric", "Value"],
            ["Total Similarity Score", f"{score:.1f}%"],
            ["Detected Sources", str(len(results.get('top_matches', [])))],
            ["Analysis Status", "Completed ✓"]
        ]
        t_summary = Table(summary_data, colWidths=[200, 200])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#64748b')),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('PADDING', (0,0), (-1,-1), 10),
            ('TEXTCOLOR', (1,1), (1,1), colors.HexColor('#ef4444') if score > 30 else colors.HexColor('#10b981'))
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 25))

        # Top Matches
        matches = results.get('top_matches', [])[:15] # Limit to top 15
        if matches:
            elements.append(Paragraph("Identified Sources (Top 15)", self.header_style))
            match_data = [["No.", "Source Identifier / Preview", "Similarity"]]
            for i, m in enumerate(matches):
                match_data.append([
                    str(i+1), 
                    Paragraph(m['title'], self.normal_style), 
                    f"{(m['score']*100):.1f}%"
                ])
            
            t_matches = Table(match_data, colWidths=[30, 380, 80])
            t_matches.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                ('ALIGN', (0,0), (0,-1), 'CENTER'),
                ('ALIGN', (2,0), (2,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(t_matches)
            elements.append(Spacer(1, 30))

        # Detailed Sentence Matching
        plag_sents = results.get('plagiarized_sentences', [])
        if plag_sents:
            elements.append(Paragraph("Detailed Sentence-level Matches", self.header_style))
            elements.append(Paragraph("The following sentences were identified as having significant similarity with existing sources.", self.normal_style))
            elements.append(Spacer(1, 10))
            
            sent_data = [["Matched Sentence", "Source / URL", "Sim %"]]
            for s in plag_sents[:30]: # Limit for readability
                percentage = s['match_score'] * 100
                source_display = s['source']
                if s.get('source_url') and s['source_url'] != 'N/A':
                    source_display = f"{s['source']}\n({s['source_url']})"
                
                sent_data.append([
                    Paragraph(f"<i>\"{s['sentence']}\"</i>", self.match_text_style),
                    Paragraph(source_display, self.normal_style),
                    f"{percentage:.1f}%"
                ])
            
            t_sents = Table(sent_data, colWidths=[300, 130, 60])
            t_sents.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f8fafc')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#64748b')),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('PADDING', (0,0), (-1,-1), 8),
            ]))
            elements.append(t_sents)
            if len(plag_sents) > 30:
                elements.append(Paragraph(f"<i>* Only showing top 30 of {len(plag_sents)} sentences.</i>", self.footer_style))
            elements.append(Spacer(1, 30))

        # Highlighted Content
        elements.append(PageBreak())
        elements.append(Paragraph("Analyzed Document Content", self.header_style))
        sanitized = self._sanitize_text(text)
        elements.append(Paragraph(sanitized, self.normal_style))

        doc.build(elements)
        buffer.seek(0)
        return buffer

    def generate_multi_report(self, doc_names, matrix, pairwise_results):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter, 
            leftMargin=50, rightMargin=50, topMargin=50, bottomMargin=50
        )
        elements = self._get_page_header("Multi-Document Comparison")

        # Inventory
        elements.append(Paragraph("Dataset Inventory", self.header_style))
        for name in doc_names:
            elements.append(Paragraph(f"• {name}", self.normal_style))
        elements.append(Spacer(1, 20))

        # Similarity Matrix
        elements.append(Paragraph("Similarity Matrix (%)", self.header_style))
        # Fixed column count for matrix - limit display for width if too many docs
        display_names = doc_names[:6] # Limit columns for A4 width
        data = [[""] + display_names]
        for name1 in display_names:
            row = [Paragraph(f"<b>{name1}</b>", self.normal_style)]
            for name2 in display_names:
                score = matrix[name1][name2]
                row.append(f"{score:.1f}")
            data.append(row)

        available_width = 500
        col_w = available_width / (len(display_names) + 1)
        t_matrix = Table(data, colWidths=[col_w] * (len(display_names) + 1))
        t_matrix.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4f46e5')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('PADDING', (0,0), (-1,-1), 6)
        ]))
        elements.append(t_matrix)
        if len(doc_names) > 6:
            elements.append(Paragraph(f"<i>* Showing top 6 of {len(doc_names)} documents in table view.</i>", self.footer_style))
        elements.append(Spacer(1, 30))

        # Detailed Pairwise Breakdown
        elements.append(Paragraph("Critical Pairwise Analysis", self.header_style))
        # Limit to top 15 pairs by similarity
        sorted_pairs = sorted(pairwise_results, key=lambda x: x['similarity_percentage'], reverse=True)[:15]

        for pair in sorted_pairs:
            elements.append(Paragraph(f"{pair['doc1']} <b>vs</b> {pair['doc2']} → <font color='#ef4444'>{pair['similarity_percentage']:.1f}%</font>", self.sub_header_style))
            
            if pair.get('matches'):
                elements.append(Paragraph("Matched Text Segments:", self.normal_style))
                # Show top 5 sentence matches per pair
                for m in pair['matches'][:5]:
                    elements.append(Paragraph(f"• {m['sentence1']}", self.match_text_style))
                    elements.append(Spacer(1, 3))
            
            elements.append(Paragraph("<hr color='#f1f5f9' width='50%'/>", self.normal_style))
            elements.append(Spacer(1, 10))

        doc.build(elements)
        buffer.seek(0)
        return buffer
