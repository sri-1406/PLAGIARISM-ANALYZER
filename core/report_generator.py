from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect
from datetime import datetime
import io
import html
import re

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that automatically computes the total page count
    and renders consistent professional running headers and footers.
    """
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
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, num_pages):
        self.saveState()
        w, h = self._pagesize
        
        # Running Header on pages > 1
        if self._pageNumber > 1:
            self.setFont('Helvetica-Bold', 8)
            self.setFillColor(colors.HexColor('#475569'))
            header_title = getattr(self, '_custom_header_title', "PLAGIARISM ANALYZER — Detailed Analysis Report")
            header_right = getattr(self, '_custom_header_right', "Textual Integrity Verification")
            self.drawString(45, h - 35, header_title)
            self.setFont('Helvetica', 8)
            self.drawRightString(w - 45, h - 35, header_right)
            
            # Subtle header divider rule
            self.setStrokeColor(colors.HexColor('#cbd5e1'))
            self.setLineWidth(0.5)
            self.line(45, h - 40, w - 45, h - 40)

        # Running Footer on ALL pages
        self.setFont('Helvetica', 8)
        self.setFillColor(colors.HexColor('#64748b'))
        self.drawString(45, 30, "CONFIDENTIAL & PROPRIETARY — Plagiarism Analyzer v2.0")
        self.drawRightString(w - 45, 30, f"Page {self._pageNumber} of {num_pages}")
        
        # Subtle footer divider rule
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.5)
        self.line(45, 40, w - 45, 40)
        
        self.restoreState()


class ReportGenerator:
    def __init__(self):
        self._init_styles()

    def _init_styles(self):
        self.styles = getSampleStyleSheet()

        self.doc_title_style = ParagraphStyle(
            'DocTitle',
            parent=self.styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=3
        )
        self.doc_subtitle_style = ParagraphStyle(
            'DocSubtitle',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=15,
            textColor=colors.HexColor('#475569'),
            spaceAfter=14
        )
        self.section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=17,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        )
        self.section_desc_style = ParagraphStyle(
            'SectionDesc',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#475569'),
            spaceAfter=8,
            keepWithNext=True
        )
        self.sub_heading_style = ParagraphStyle(
            'SubHeading',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor('#0f172a'),
            spaceBefore=12,
            spaceAfter=6,
            keepWithNext=True
        )
        self.meta_val_style = ParagraphStyle(
            'MetaVal',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.HexColor('#334155')
        )
        self.tbl_cell = ParagraphStyle(
            'TblCell',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        )
        self.tbl_cell_bold = ParagraphStyle(
            'TblCellBold',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#1e293b')
        )
        self.tbl_hdr = ParagraphStyle(
            'TblHdr',
            parent=self.styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=11.5,
            textColor=colors.white
        )
        self.match_submitted_style = ParagraphStyle(
            'MatchSub',
            parent=self.styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=colors.HexColor('#334155')
        )
        self.doc_content_style = ParagraphStyle(
            'DocContent',
            parent=self.styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor('#1e293b')
        )

    def _make_squares(self, score):
        num_squares = max(1, min(10, round(score / 5)))
        d = Drawing(120, 10)
        for i in range(num_squares):
            d.add(Rect(i * 12, 1, 9, 8, fillColor=colors.HexColor('#4338ca'), strokeColor=None))
        return d

    def _highlight_text(self, raw_text, highlighted_matches):
        if not raw_text:
            return []
        
        spans = []
        for m in highlighted_matches:
            s = m.get('sentence', '')
            if not s:
                continue
            score = float(m.get('similarity_percentage') or (m.get('match_score', 0) * 100 if m.get('match_score', 0) <= 1.0 else m.get('match_score', 0)))
            start = raw_text.find(s)
            if start != -1:
                spans.append((start, start + len(s), score, s))
                
        spans.sort(key=lambda x: x[0])
        non_overlapping = []
        last_end = 0
        for start, end, score, s in spans:
            if start >= last_end:
                non_overlapping.append((start, end, score, s))
                last_end = end

        chunks = []
        curr_pos = 0
        for start, end, score, s in non_overlapping:
            if start > curr_pos:
                chunks.append(('unmatched', raw_text[curr_pos:start], 0.0))
            chunks.append(('matched', s, score))
            curr_pos = end
        if curr_pos < len(raw_text):
            chunks.append(('unmatched', raw_text[curr_pos:], 0.0))

        html_parts = []
        for kind, content, score in chunks:
            escaped = html.escape(content).replace('\n', '<br/>')
            if kind == 'matched' and score >= 10.0:
                if score >= 70.0:
                    color = '#dc2626'
                elif score >= 40.0:
                    color = '#ea580c'
                else:
                    color = '#0d9488'
                html_parts.append(f'<b><font color="{color}">{escaped}</font></b> <font color="{color}">[{score:.1f}%]</font>')
            else:
                html_parts.append(f'<font color="#1e293b">{escaped}</font>')
                
        full_html = "".join(html_parts)
        paragraphs_html = [p.strip() for p in full_html.split('<br/><br/>') if p.strip()]
        return paragraphs_html

    def generate_single_report(self, text, results, filename=None, report_id=None, file_type=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=45, rightMargin=45,
            topMargin=50, bottomMargin=50
        )

        # Extract dynamic metadata
        raw_id = report_id or results.get('report_id') or datetime.now().strftime("%Y-%m-%d")
        report_id_str = str(raw_id)
        if not report_id_str.startswith("PA-"):
            report_id_str = f"PA-2026-{report_id_str}"

        file_name_str = filename or results.get('file_name') or results.get('filename') or "Submitted Document.pdf"
        file_type_str = file_type or results.get('file_type') or (file_name_str.split('.')[-1].upper() if '.' in file_name_str else "PDF")
        analysis_date_str = results.get('analysis_date') or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        status_str = results.get('analysis_status') or "Completed"
        
        overall_pct = float(results.get('overall_percentage') or results.get('plagiarism_percentage') or 0.0)
        unique_pct = float(results.get('original_percentage') or results.get('unmatched_percentage') or max(0.0, 100.0 - overall_pct))
        
        sim_level_str = results.get('similarity_level')
        if not sim_level_str:
            if overall_pct >= 70: sim_level_str = "High Similarity"
            elif overall_pct >= 40: sim_level_str = "Moderate Similarity"
            elif overall_pct >= 10: sim_level_str = "Low Similarity"
            else: sim_level_str = "Original Content"
            
        sentence_matches = results.get('highlighted_matches') or results.get('plagiarized_sentences') or results.get('matches') or []
        sources = results.get('top_matches') or results.get('sources') or []
        
        total_sents = int(results.get('total_sentences_count') or results.get('total_sentences') or results.get('statistics', {}).get('total_sentences') or len(sentence_matches))
        analyzed_sents = int(results.get('analyzed_sentences_count') or results.get('statistics', {}).get('analyzed_sentences') or total_sents)
        matched_sents = int(results.get('matched_sentences_count') or results.get('matched_sentences') or results.get('scoring_count') or results.get('statistics', {}).get('matching_sentences') or len(sentence_matches))
        unique_sents = int(results.get('unique_sentences_count') or results.get('statistics', {}).get('unique_sentences') or max(0, total_sents - matched_sents))
        detected_sources_count = int(results.get('sources_detected_count') or results.get('statistics', {}).get('sources_detected') or len(sources))
        
        highest_sentence_sim = float(results.get('highest_sentence_similarity') or results.get('statistics', {}).get('highest_sentence_similarity') or 0.0)
        if highest_sentence_sim == 0.0 and sentence_matches:
            highest_sentence_sim = max([float(m.get('similarity_percentage') or (m.get('match_score', 0) * 100 if m.get('match_score', 0) <= 1.0 else m.get('match_score', 0))) for m in sentence_matches] or [0.0])
            
        avg_sentence_sim = float(results.get('average_sentence_similarity') or results.get('average_similarity') or results.get('statistics', {}).get('average_sentence_similarity') or 0.0)
        if avg_sentence_sim == 0.0 and sentence_matches:
            scores = [float(m.get('similarity_percentage') or (m.get('match_score', 0) * 100 if m.get('match_score', 0) <= 1.0 else m.get('match_score', 0))) for m in sentence_matches]
            avg_sentence_sim = sum(scores) / len(scores) if scores else 0.0

        overlap_pct = (matched_sents / total_sents * 100) if total_sents > 0 else 0.0

        story = []
        
        # ==================== PAGE 1 ====================
        story.append(Paragraph("PLAGIARISM ANALYZER", self.doc_title_style))
        story.append(Paragraph("Detailed Textual Similarity & Analysis Report", self.doc_subtitle_style))
        
        # Meta Box
        meta_table = Table([
            [
                Paragraph(f"<b>Report ID:</b> {report_id_str}", self.meta_val_style),
                Paragraph(f"<b>Analysis Date:</b> {analysis_date_str}", self.meta_val_style)
            ],
            [
                Paragraph(f"<b>Uploaded File:</b> {file_name_str}", self.meta_val_style),
                Paragraph(f"<b>Status:</b> <font color='#16a34a'><b>{status_str}</b></font>", self.meta_val_style)
            ],
            [
                Paragraph(f"<b>File Type:</b> {file_type_str}", self.meta_val_style),
                Paragraph(f"<b>Analysis Mode:</b> Single Document Analysis", self.meta_val_style)
            ]
        ], colWidths=[252.5, 252.5])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Section 1
        story.append(Paragraph("1. Overall Analysis Summary", self.section_heading_style))
        
        sec1_data = [
            [Paragraph("Metric Description", self.tbl_hdr), Paragraph("Calculated Value", self.tbl_hdr), Paragraph("Status / Classification", self.tbl_hdr)],
            [Paragraph("Overall Similarity Score", self.tbl_cell), Paragraph(f"<b>{overall_pct:.1f}%</b>", self.tbl_cell), Paragraph(f"{sim_level_str}", self.tbl_cell)],
            [Paragraph("Original / Unique Content", self.tbl_cell), Paragraph(f"<b><font color='#16a34a'>{unique_pct:.1f}%</font></b>", self.tbl_cell), Paragraph("Unmatched Text", self.tbl_cell)],
            [Paragraph("Detected Reference Sources", self.tbl_cell), Paragraph(f"<b>{detected_sources_count} sources</b>", self.tbl_cell), Paragraph("Dataset Matches", self.tbl_cell)],
            [Paragraph("Matching Sentences", self.tbl_cell), Paragraph(f"<b>{matched_sents} / {total_sents} sentences</b>", self.tbl_cell), Paragraph(f"<b>{overlap_pct:.1f}% sentence overlap</b>", self.tbl_cell)],
            [Paragraph("Highest Sentence Similarity", self.tbl_cell), Paragraph(f"<b>{highest_sentence_sim:.1f}% peak match</b>", self.tbl_cell), Paragraph("Maximum single match", self.tbl_cell)],
            [Paragraph("Analysis Execution Status", self.tbl_cell), Paragraph("<b>Completed ✓</b>", self.tbl_cell), Paragraph("Full pipeline executed", self.tbl_cell)],
        ]
        t_sec1 = Table(sec1_data, colWidths=[185, 140, 180])
        t_sec1.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_sec1)
        story.append(Spacer(1, 14))

        # Disclaimer Box
        disclaimer_table = Table([
            [
                Paragraph(
                    f"<b>SIMILARITY LEVEL CLASSIFICATION: <font color='#d97706'>{sim_level_str.upper()}</font></b><br/><br/>"
                    f"<i>Disclaimer: Overall similarity represents the calculated similarity across the analyzed document, while sentence-level similarity represents the similarity of an individual matched sentence or section. The system detected textual similarity; this report does not make a final academic or disciplinary judgment.</i>",
                    ParagraphStyle('Disc', parent=self.styles['Normal'], fontName='Helvetica', fontSize=8, leading=11.5, textColor=colors.HexColor('#475569'))
                )
            ]
        ], colWidths=[505])
        disclaimer_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d97706')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fffbeb')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(disclaimer_table)
        
        # Page 1 Break
        story.append(PageBreak())

        # ==================== PAGE 2 ====================
        story.append(Paragraph("2. Source-wise Similarity Analysis", self.section_heading_style))
        story.append(Paragraph("The following table details all reference sources from the indexed database that matched against the submitted document, ordered by similarity percentage descending.", self.section_desc_style))
        
        sec2_headers = [Paragraph("Rank", self.tbl_hdr), Paragraph("Source Title", self.tbl_hdr), Paragraph("Similarity %", self.tbl_hdr), Paragraph("Level", self.tbl_hdr), Paragraph("Source ID / URL", self.tbl_hdr)]
        sec2_rows = [sec2_headers]
        
        for i, s in enumerate(sources[:10]):
            title = s.get('title') or s.get('name') or f"Source {i+1}"
            score = float(s.get('similarity_percentage') or (s.get('score', 0) * 100 if s.get('score', 0) <= 1.0 else s.get('score', 0)))
            level = s.get('similarity_level') or s.get('plagiarism_level') or s.get('level')
            if not level or level == 'None':
                if score >= 70: level = "High Similarity"
                elif score >= 40: level = "Low Similarity"
                elif score >= 10: level = "Low Similarity"
                else: level = "Original Content"
            url = s.get('source_url') or s.get('url') or 'N/A'
            
            sec2_rows.append([
                Paragraph(f"#{i+1}", self.tbl_cell_bold),
                Paragraph(html.escape(title), self.tbl_cell),
                Paragraph(f"{score:.1f}%", self.tbl_cell_bold),
                Paragraph(level, self.tbl_cell),
                Paragraph(f"<font color='#2563eb'>{html.escape(url)}</font>", ParagraphStyle('UrlStyle', parent=self.tbl_cell, fontSize=7, leading=9))
            ])
        
        t_sec2 = Table(sec2_rows, colWidths=[35, 175, 75, 80, 140])
        t_sec2.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (2,0), (3,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_sec2)
        story.append(Spacer(1, 14))

        # Breakdown Chart
        story.append(Paragraph("Source Similarity Breakdown Chart", self.sub_heading_style))
        chart_headers = [Paragraph("Source Name", self.tbl_hdr), Paragraph("Similarity Weight Visualizer", self.tbl_hdr), Paragraph("Score", self.tbl_hdr)]
        chart_rows = [chart_headers]
        for s in sources[:5]:
            title = s.get('title') or s.get('name') or 'Source'
            score = float(s.get('similarity_percentage') or (s.get('score', 0) * 100 if s.get('score', 0) <= 1.0 else s.get('score', 0)))
            chart_rows.append([
                Paragraph(html.escape(title), self.tbl_cell),
                self._make_squares(score),
                Paragraph(f"<b>{score:.1f}%</b>", self.tbl_cell_bold)
            ])
        t_chart = Table(chart_rows, colWidths=[180, 245, 80])
        t_chart.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (2,0), (2,-1), 'CENTER'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_chart)
        
        # Page 2 Break
        story.append(PageBreak())

        # ==================== PAGES 3–5: SECTION 3 ====================
        story.append(Paragraph("3. Sentence-Level Similarity Analysis", self.section_heading_style))
        story.append(Paragraph("Individual sentences and passages identified with textual similarity against indexed reference sources.", self.section_desc_style))
        
        # Show top 20 sentence matches to maintain clean pagination
        display_matches = sentence_matches[:20]
        if not display_matches:
            story.append(Paragraph("<i>No significant sentence-level similarities detected in the document.</i>", self.section_desc_style))
            story.append(Spacer(1, 15))
        else:
            for i, m in enumerate(display_matches):
                sent_text = m.get('sentence', '')
                score = float(m.get('similarity_percentage') or (m.get('match_score', 0) * 100 if m.get('match_score', 0) <= 1.0 else m.get('match_score', 0)))
                level = m.get('similarity_level') or m.get('plagiarism_level') or ("High Similarity" if score >= 70 else "Moderate Similarity" if score >= 40 else "Low Similarity")
                severity = m.get('severity') or ("High" if score >= 70 else "Medium" if score >= 40 else "Low")
                src_title = m.get('source') or "Indexed Source"
                src_url = m.get('source_url') or "N/A"
                
                color_sev = '#dc2626' if severity == 'High' else '#d97706' if severity == 'Medium' else '#0d9488'
                
                card_data = [
                    [
                        Paragraph(f"<b>MATCH #{i+1}</b>", self.tbl_cell_bold),
                        Paragraph(f"Similarity: <b>{score:.1f}%</b> ({level}) | Severity: <font color='{color_sev}'><b>{severity}</b></font>", self.tbl_cell)
                    ],
                    [
                        Paragraph("<b>Submitted Document Text:</b>", self.tbl_cell_bold),
                        Paragraph(f"\"{html.escape(sent_text)}\"", self.match_submitted_style)
                    ],
                    [
                        Paragraph("<b>Matched Reference Source:</b>", self.tbl_cell_bold),
                        Paragraph(f"<b>{html.escape(src_title)}</b><br/><font color='#2563eb'>{html.escape(src_url)}</font>", self.tbl_cell)
                    ]
                ]
                t_card = Table(card_data, colWidths=[130, 375])
                t_card.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#f1f5f9')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('TOPPADDING', (0,0), (-1,-1), 4),
                    ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ('LEFTPADDING', (0,0), (-1,-1), 6),
                    ('RIGHTPADDING', (0,0), (-1,-1), 6),
                ]))
                
                story.append(t_card)
                story.append(Spacer(1, 5))

        # Page Break for Section 4
        story.append(PageBreak())

        # ==================== PAGES 6–9: SECTION 4 ====================
        story.append(Paragraph("4. Highlighted Document Content", self.section_heading_style))
        story.append(Paragraph("Below is the analyzed document text with sentence matches highlighted according to similarity intensity.", self.section_desc_style))
        
        # Legend
        legend_data = [[
            Paragraph("<font color='#dc2626'>■</font> <b>High Similarity (≥ 70%)</b>", self.tbl_cell),
            Paragraph("<font color='#ea580c'>■</font> <b>Medium Similarity (40–69%)</b>", self.tbl_cell),
            Paragraph("<font color='#0d9488'>■</font> <b>Low Similarity (10–39%)</b>", self.tbl_cell),
            Paragraph("<font color='#475569'>■</font> <b>Original Text (&lt; 10%)</b>", self.tbl_cell)
        ]]
        t_legend = Table(legend_data, colWidths=[126, 126, 126, 127])
        t_legend.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_legend)
        story.append(Spacer(1, 10))

        # Highlighted Content Paragraphs
        paras = self._highlight_text(text, sentence_matches)
        for p in paras:
            story.append(Paragraph(p, self.doc_content_style))
            story.append(Spacer(1, 4))
            
        # Page Break for Section 5
        story.append(PageBreak())

        # ==================== PAGE 10: SECTION 5 ====================
        story.append(Paragraph("5. Matching Statistics & Metrics", self.section_heading_style))
        story.append(Paragraph("Comprehensive statistical metrics calculated across the analyzed document text.", self.section_desc_style))
        
        stats_data = [
            [Paragraph("Statistical Metric", self.tbl_hdr), Paragraph("Calculated Value", self.tbl_hdr), Paragraph("Technical Context", self.tbl_hdr)],
            [Paragraph("Total Sentences", self.tbl_cell), Paragraph(f"<b>{total_sents}</b>", self.tbl_cell_bold), Paragraph("Raw document sentence count", self.tbl_cell)],
            [Paragraph("Analyzed Sentences", self.tbl_cell), Paragraph(f"<b>{analyzed_sents}</b>", self.tbl_cell_bold), Paragraph("Sentences evaluated by TF-IDF engine", self.tbl_cell)],
            [Paragraph("Matching Sentences", self.tbl_cell), Paragraph(f"<b>{matched_sents}</b>", self.tbl_cell_bold), Paragraph("Sentences exceeding similarity threshold", self.tbl_cell)],
            [Paragraph("Unique Sentences", self.tbl_cell), Paragraph(f"<b>{unique_sents}</b>", self.tbl_cell_bold), Paragraph("Original, non-matching content sentences", self.tbl_cell)],
            [Paragraph("Detected Sources Count", self.tbl_cell), Paragraph(f"<b>{detected_sources_count}</b>", self.tbl_cell_bold), Paragraph("Distinct reference sources matched", self.tbl_cell)],
            [Paragraph("Highest Sentence Similarity", self.tbl_cell), Paragraph(f"<b>{highest_sentence_sim:.1f}%</b>", self.tbl_cell_bold), Paragraph("Peak single sentence similarity score", self.tbl_cell)],
            [Paragraph("Average Sentence Similarity", self.tbl_cell), Paragraph(f"<b>{avg_sentence_sim:.1f}%</b>", self.tbl_cell_bold), Paragraph("Mean similarity across matched sentences", self.tbl_cell)],
            [Paragraph("Overall Document Similarity", self.tbl_cell), Paragraph(f"<b>{overall_pct:.1f}%</b>", self.tbl_cell_bold), Paragraph("Composite weighted similarity score", self.tbl_cell)],
        ]
        t_stats = Table(stats_data, colWidths=[170, 110, 225])
        t_stats.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 6),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_stats)
        
        # Page Break for Section 6, 7, 8
        story.append(PageBreak())

        # ==================== PAGE 11: SECTION 6, 7, 8 ====================
        story.append(Paragraph("6. Technical Detection Method", self.section_heading_style))
        story.append(Paragraph("The analysis pipeline executes the following 10-stage processing pipeline using active project algorithms:", self.section_desc_style))
        
        method_data = [
            [Paragraph("Execution Stage", self.tbl_hdr), Paragraph("Implementation Algorithm & Tool", self.tbl_hdr)],
            [Paragraph("Stage 1.", self.tbl_cell_bold), Paragraph("Document Text Extraction (.pdf, .docx, .txt)", self.tbl_cell)],
            [Paragraph("Stage 2.", self.tbl_cell_bold), Paragraph("Text Preprocessing & Cleaning", self.tbl_cell)],
            [Paragraph("Stage 3.", self.tbl_cell_bold), Paragraph("Sentence Tokenization (NLTK sent_tokenize)", self.tbl_cell)],
            [Paragraph("Stage 4.", self.tbl_cell_bold), Paragraph("Word Tokenization & Normalization (NLTK word_tokenize)", self.tbl_cell)],
            [Paragraph("Stage 5.", self.tbl_cell_bold), Paragraph("Stop-word Removal (NLTK English stopwords)", self.tbl_cell)],
            [Paragraph("Stage 6.", self.tbl_cell_bold), Paragraph("TF-IDF Vectorization (scikit-learn TfidfVectorizer)", self.tbl_cell)],
            [Paragraph("Stage 7.", self.tbl_cell_bold), Paragraph("Cosine Similarity Calculation", self.tbl_cell)],
            [Paragraph("Stage 8.", self.tbl_cell_bold), Paragraph("Jaccard Similarity Token Overlap", self.tbl_cell)],
            [Paragraph("Stage 9.", self.tbl_cell_bold), Paragraph("Sentence & Sliding Window Unit Comparison", self.tbl_cell)],
            [Paragraph("Stage 10.", self.tbl_cell_bold), Paragraph("Similarity Level Classification", self.tbl_cell)],
        ]
        t_method = Table(method_data, colWidths=[130, 375])
        t_method.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_method)
        story.append(Spacer(1, 6))

        # Future Enhancements Box
        enh_table = Table([
            [
                Paragraph(
                    "<font color='#475569'><b><i>PROPOSED FUTURE ENHANCEMENTS (Not currently active in execution):</i></b><br/>"
                    "• Deep Learning Semantic Embeddings (Sentence-BERT / Transformer Models)<br/>"
                    "• Scalable Vector Database Indexing (MongoDB / Faiss)</font>",
                    self.tbl_cell
                )
            ]
        ], colWidths=[505])
        enh_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(enh_table)
        story.append(Spacer(1, 10))

        # Section 7: Conclusion
        story.append(Paragraph("7. Analysis Conclusion", self.section_heading_style))
        conc_table = Table([
            [
                Paragraph(
                    "<font color='#4338ca'><b>CONCLUSION STATEMENT:</b></font><br/>"
                    f"The analysis detected textual similarities between the submitted document and the identified sources. The calculated overall similarity was <b>{overall_pct:.1f}%</b>. Detailed source-wise and sentence-level matches are provided in this report for further review.",
                    ParagraphStyle('Conc', parent=self.tbl_cell, fontSize=8.5, leading=12)
                )
            ]
        ], colWidths=[505])
        conc_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#6366f1')),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(conc_table)
        story.append(Spacer(1, 10))

        # Section 8: Technical System Metadata
        story.append(Paragraph("8. Technical System Metadata", self.section_heading_style))
        meta_sys_data = [
            [Paragraph("<b>Report Identifier:</b>", self.tbl_cell_bold), Paragraph(f"{report_id_str}", self.tbl_cell)],
            [Paragraph("<b>Database Engine:</b>", self.tbl_cell_bold), Paragraph("SQLite3 (database.db)", self.tbl_cell)],
            [Paragraph("<b>NLP Frameworks:</b>", self.tbl_cell_bold), Paragraph("NLTK, scikit-learn, TF-IDF Vectorizer", self.tbl_cell)],
            [Paragraph("<b>Application Version:</b>", self.tbl_cell_bold), Paragraph("Plagiarism Analyzer v2.0 (Flask)", self.tbl_cell)],
        ]
        t_sys_meta = Table(meta_sys_data, colWidths=[160, 345])
        t_sys_meta.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_sys_meta)

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer

    def generate_multi_report(self, doc_names, matrix, pairwise_results, report_id=None):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            leftMargin=45, rightMargin=45,
            topMargin=50, bottomMargin=50
        )

        raw_id = report_id or datetime.now().strftime("%Y%m%d%H%M")
        report_id_str = f"PA-MD-{raw_id}" if not str(raw_id).startswith("PA-MD-") else str(raw_id)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        num_docs = len(doc_names)
        num_pairs = len(pairwise_results)
        
        pair_scores = [p.get('similarity_percentage', 0.0) for p in pairwise_results]
        max_sim = max(pair_scores) if pair_scores else 0.0
        avg_sim = (sum(pair_scores) / len(pair_scores)) if pair_scores else 0.0
        high_pairs = sum(1 for s in pair_scores if s >= 70.0)
        mod_pairs = sum(1 for s in pair_scores if 40.0 <= s < 70.0)

        story = []

        # Running canvas title
        def set_custom_canvas(canvas_obj):
            canvas_obj._custom_header_title = "PLAGIARISM ANALYZER — Multi-Document Comparison Report"
            canvas_obj._custom_header_right = "Cross-Corpus Integrity Verification"

        # ==================== PAGE 1 ====================
        story.append(Paragraph("PLAGIARISM ANALYZER", self.doc_title_style))
        story.append(Paragraph("Detailed Multi-Document Similarity Analysis Report", self.doc_subtitle_style))

        # Metadata Table
        meta_table = Table([
            [
                Paragraph(f"<b>Report ID:</b> {report_id_str}", self.meta_val_style),
                Paragraph(f"<b>Analysis Date:</b> {now_str}", self.meta_val_style)
            ],
            [
                Paragraph(f"<b>Documents Analyzed:</b> {num_docs} files", self.meta_val_style),
                Paragraph(f"<b>Status:</b> <font color='#16a34a'><b>Completed ✓</b></font>", self.meta_val_style)
            ],
            [
                Paragraph("<b>Analysis Mode:</b> Multi-Document Comparison", self.meta_val_style),
                Paragraph("<b>Engine:</b> TF-IDF + Cosine Alignment", self.meta_val_style)
            ]
        ], colWidths=[252.5, 252.5])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 14))

        # Section 1: Overview Summary
        story.append(Paragraph("1. Overall Comparison Summary", self.section_heading_style))
        summary_data = [
            [Paragraph("Metric Description", self.tbl_hdr), Paragraph("Calculated Value", self.tbl_hdr), Paragraph("Status / Classification", self.tbl_hdr)],
            [Paragraph("Total Documents Compared", self.tbl_cell), Paragraph(f"<b>{num_docs} documents</b>", self.tbl_cell_bold), Paragraph("Uploaded document collection", self.tbl_cell)],
            [Paragraph("Total Document Pairs", self.tbl_cell), Paragraph(f"<b>{num_pairs} pairs</b>", self.tbl_cell_bold), Paragraph("Cross-comparison evaluations", self.tbl_cell)],
            [Paragraph("Highest Pairwise Similarity", self.tbl_cell), Paragraph(f"<b>{max_sim:.1f}%</b>", self.tbl_cell_bold), Paragraph("Peak cross-document match", self.tbl_cell)],
            [Paragraph("Average Inter-Document Similarity", self.tbl_cell), Paragraph(f"<b>{avg_sim:.1f}%</b>", self.tbl_cell_bold), Paragraph("Mean cross-similarity score", self.tbl_cell)],
            [Paragraph("High Similarity Pairs (≥ 70%)", self.tbl_cell), Paragraph(f"<b>{high_pairs} pairs</b>", self.tbl_cell_bold), Paragraph("Flagged critical duplicates" if high_pairs else "None detected", self.tbl_cell)],
            [Paragraph("Moderate Similarity Pairs (40–69%)", self.tbl_cell), Paragraph(f"<b>{mod_pairs} pairs</b>", self.tbl_cell_bold), Paragraph("Potential partial overlap" if mod_pairs else "None detected", self.tbl_cell)],
        ]
        t_summary = Table(summary_data, colWidths=[185, 140, 180])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#3b82f6')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(t_summary)
        story.append(Spacer(1, 14))

        # Multi-doc Disclaimer
        disclaimer_table = Table([
            [
                Paragraph(
                    "<b>ANALYSIS CLASSIFICATION: MULTI-DOCUMENT COMPARATIVE MATRIX</b><br/><br/>"
                    "<i>Disclaimer: Cross-document similarity evaluates shared vocabulary and sentence alignment across all uploaded documents. Higher percentages indicate substantial textual reuse or shared sections between authors.</i>",
                    ParagraphStyle('DiscMD', parent=self.styles['Normal'], fontName='Helvetica', fontSize=8, leading=11.5, textColor=colors.HexColor('#475569'))
                )
            ]
        ], colWidths=[505])
        disclaimer_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#d97706')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#fffbeb')),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(disclaimer_table)
        story.append(Spacer(1, 14))

        # Section 2: Similarity Matrix & Rankings
        story.append(Paragraph("2. Pairwise Comparison Matrix & Rankings", self.section_heading_style))
        story.append(Paragraph("Cross-document cosine similarity matrix (%) and ranking of document pairs by descending similarity score.", self.section_desc_style))

        # Matrix Table
        display_docs = doc_names[:6]
        col_w = 505 / (len(display_docs) + 1)
        matrix_data = [[Paragraph("<b>Document</b>", self.tbl_hdr)] + [Paragraph(f"<b>{d[:12]}..</b>" if len(d)>14 else f"<b>{d}</b>", self.tbl_hdr) for d in display_docs]]
        
        for d1 in display_docs:
            row = [Paragraph(f"<b>{d1[:14]}..</b>" if len(d1)>16 else f"<b>{d1}</b>", self.tbl_cell_bold)]
            for d2 in display_docs:
                val = matrix.get(d1, {}).get(d2, 0.0)
                color = '#dc2626' if val >= 70 else '#ea580c' if val >= 40 else '#1e293b'
                row.append(Paragraph(f"<font color='{color}'><b>{val:.1f}%</b></font>" if val > 0 else "0.0%", self.tbl_cell))
            matrix_data.append(row)
            
        t_matrix = Table(matrix_data, colWidths=[col_w] * (len(display_docs) + 1))
        t_matrix.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('ALIGN', (1,1), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ]))
        story.append(t_matrix)
        story.append(Spacer(1, 14))

        # Rankings Table
        story.append(Paragraph("Pairwise Comparison Rankings", self.sub_heading_style))
        rank_headers = [Paragraph("Rank", self.tbl_hdr), Paragraph("Document A", self.tbl_hdr), Paragraph("Document B", self.tbl_hdr), Paragraph("Similarity %", self.tbl_hdr), Paragraph("Level", self.tbl_hdr), Paragraph("Matches", self.tbl_hdr)]
        rank_rows = [rank_headers]

        sorted_pairs = sorted(pairwise_results, key=lambda x: x.get('similarity_percentage', 0), reverse=True)
        for idx, p in enumerate(sorted_pairs[:15]):
            score = float(p.get('similarity_percentage', 0))
            level = "High Similarity" if score >= 70 else "Moderate Similarity" if score >= 40 else "Low Similarity" if score >= 10 else "Original Content"
            m_count = p.get('matching_sentences_count', len(p.get('matches', [])))
            color = '#dc2626' if score >= 70 else '#ea580c' if score >= 40 else '#1e293b'

            rank_rows.append([
                Paragraph(f"#{idx+1}", self.tbl_cell_bold),
                Paragraph(html.escape(p.get('doc1', 'Doc A')), self.tbl_cell),
                Paragraph(html.escape(p.get('doc2', 'Doc B')), self.tbl_cell),
                Paragraph(f"<font color='{color}'><b>{score:.1f}%</b></font>", self.tbl_cell_bold),
                Paragraph(level, self.tbl_cell),
                Paragraph(f"{m_count} sents", self.tbl_cell)
            ])

        t_ranks = Table(rank_rows, colWidths=[35, 140, 140, 65, 75, 50])
        t_ranks.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('ALIGN', (0,0), (0,-1), 'CENTER'),
            ('ALIGN', (3,0), (5,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
            ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(t_ranks)

        # PageBreak to Section 3
        story.append(PageBreak())

        # ==================== SECTION 3: PAIRWISE DETAILS ====================
        story.append(Paragraph("3. Detailed Pairwise Similarity Results", self.section_heading_style))
        story.append(Paragraph("Individual matching sentence passages and alignments identified across document pairs.", self.section_desc_style))

        for idx, p in enumerate(sorted_pairs[:10]):
            score = float(p.get('similarity_percentage', 0))
            level = "High Similarity" if score >= 70 else "Moderate Similarity" if score >= 40 else "Low Similarity"
            color_sev = '#dc2626' if score >= 70 else '#d97706' if score >= 40 else '#0d9488'

            pair_header = Table([
                [
                    Paragraph(f"<b>PAIR #{idx+1}: {html.escape(p.get('doc1'))} vs {html.escape(p.get('doc2'))}</b>", self.tbl_cell_bold),
                    Paragraph(f"Similarity: <b>{score:.1f}%</b> (<font color='{color_sev}'><b>{level}</b></font>)", self.tbl_cell)
                ]
            ], colWidths=[335, 170])
            pair_header.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
                ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                ('PADDING', (0,0), (-1,-1), 5),
            ]))
            story.append(pair_header)

            matches = p.get('matches', [])
            if matches:
                m_table_data = [[
                    Paragraph("#", self.tbl_hdr),
                    Paragraph(f"Segment from {html.escape(p.get('doc1')[:20])}", self.tbl_hdr),
                    Paragraph(f"Segment from {html.escape(p.get('doc2')[:20])}", self.tbl_hdr),
                    Paragraph("Sim %", self.tbl_hdr)
                ]]
                for m_idx, m in enumerate(matches[:8]):
                    m_score = float(m.get('similarity_percentage') or m.get('score', 0))
                    m_table_data.append([
                        Paragraph(str(m_idx+1), self.tbl_cell_bold),
                        Paragraph(f"\"{html.escape(m.get('sentence1', ''))}\"", self.match_submitted_style),
                        Paragraph(f"\"{html.escape(m.get('sentence2', ''))}\"", self.match_submitted_style),
                        Paragraph(f"<b>{m_score:.1f}%</b>", self.tbl_cell_bold)
                    ])
                t_matches = Table(m_table_data, colWidths=[25, 220, 220, 40])
                t_matches.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#475569')),
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('ALIGN', (0,0), (0,-1), 'CENTER'),
                    ('ALIGN', (3,0), (3,-1), 'CENTER'),
                    ('PADDING', (0,0), (-1,-1), 4),
                ]))
                story.append(t_matches)
            else:
                empty_t = Table([[Paragraph("<i>No specific sentence segment overlaps detected between this pair.</i>", self.section_desc_style)]], colWidths=[505])
                empty_t.setStyle(TableStyle([
                    ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
                    ('BACKGROUND', (0,0), (-1,-1), colors.white),
                    ('PADDING', (0,0), (-1,-1), 6),
                ]))
                story.append(empty_t)
            
            story.append(Spacer(1, 10))

        # PageBreak to Section 4, 5, 6
        story.append(PageBreak())

        # ==================== TECHNICAL DETECTION METHOD & CONCLUSION ====================
        story.append(Paragraph("4. Technical Detection Method (Multi-Compare)", self.section_heading_style))
        story.append(Paragraph("The comparative engine executes the following multi-document processing pipeline:", self.section_desc_style))

        multi_pipeline_data = [
            [Paragraph("Execution Stage", self.tbl_hdr), Paragraph("Implementation Algorithm & Tool", self.tbl_hdr)],
            [Paragraph("Stage 1.", self.tbl_cell_bold), Paragraph("Multi-Document Text Extraction (.pdf, .docx, .txt)", self.tbl_cell)],
            [Paragraph("Stage 2.", self.tbl_cell_bold), Paragraph("Cross-Document Text Normalization & Tokenization", self.tbl_cell)],
            [Paragraph("Stage 3.", self.tbl_cell_bold), Paragraph("Corpus-Wide TF-IDF Vector Space Construction", self.tbl_cell)],
            [Paragraph("Stage 4.", self.tbl_cell_bold), Paragraph("N×N Symmetric Cosine Similarity Cross-Multiplication", self.tbl_cell)],
            [Paragraph("Stage 5.", self.tbl_cell_bold), Paragraph("Pairwise Sentence Alignment & Sliding Window Extraction", self.tbl_cell)],
            [Paragraph("Stage 6.", self.tbl_cell_bold), Paragraph("Cross-Document Plagiarism Classification & Anomaly Detection", self.tbl_cell)],
        ]
        t_multi_pipe = Table(multi_pipeline_data, colWidths=[130, 375])
        t_multi_pipe.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e293b')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_multi_pipe)
        story.append(Spacer(1, 8))

        # Future Enhancements Box
        enh_table = Table([
            [
                Paragraph(
                    "<font color='#475569'><b><i>PROPOSED FUTURE ENHANCEMENTS (Not currently active in execution):</i></b><br/>"
                    "• Graph-based Document Collusion Detection Networks<br/>"
                    "• Cross-Lingual Semantic Matching via Multilingual Transformers</font>",
                    self.tbl_cell
                )
            ]
        ], colWidths=[505])
        enh_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('PADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(enh_table)
        story.append(Spacer(1, 10))

        # Section 5: Conclusion
        story.append(Paragraph("5. Analysis Conclusion", self.section_heading_style))
        conc_text = (
            f"The multi-document comparative analysis evaluated {num_docs} documents across {num_pairs} distinct pairwise combinations. "
            f"The peak pairwise similarity detected was <b>{max_sim:.1f}%</b>, with an inter-corpus average of <b>{avg_sim:.1f}%</b>. "
            f"A total of {high_pairs} pairs showed high similarity (≥ 70%), and {mod_pairs} pairs showed moderate similarity (40–69%). "
            "Inspect the detailed pairwise alignments above for complete section-by-section breakdown."
        )
        conc_table = Table([
            [
                Paragraph(
                    "<font color='#4338ca'><b>CONCLUSION STATEMENT:</b></font><br/>" + conc_text,
                    ParagraphStyle('ConcMD', parent=self.tbl_cell, fontSize=8.5, leading=12)
                )
            ]
        ], colWidths=[505])
        conc_table.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#6366f1')),
            ('BACKGROUND', (0,0), (-1,-1), colors.white),
            ('PADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(conc_table)
        story.append(Spacer(1, 10))

        # Section 6: Technical System Metadata
        story.append(Paragraph("6. Technical System Metadata", self.section_heading_style))
        meta_sys_data = [
            [Paragraph("<b>Report Identifier:</b>", self.tbl_cell_bold), Paragraph(f"{report_id_str}", self.tbl_cell)],
            [Paragraph("<b>Database Engine:</b>", self.tbl_cell_bold), Paragraph("SQLite3 (database.db)", self.tbl_cell)],
            [Paragraph("<b>NLP Frameworks:</b>", self.tbl_cell_bold), Paragraph("NLTK, scikit-learn, TF-IDF Vectorizer", self.tbl_cell)],
            [Paragraph("<b>Application Version:</b>", self.tbl_cell_bold), Paragraph("Plagiarism Analyzer v2.0 (Flask)", self.tbl_cell)],
        ]
        t_sys_meta = Table(meta_sys_data, colWidths=[160, 345])
        t_sys_meta.setStyle(TableStyle([
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f8fafc')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 4.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 4.5),
            ('LEFTPADDING', (0,0), (-1,-1), 6),
            ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t_sys_meta)

        # Build document
        doc.build(story, canvasmaker=NumberedCanvas)
        buffer.seek(0)
        return buffer
