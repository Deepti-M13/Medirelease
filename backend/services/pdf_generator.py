from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from datetime import datetime
import io


def generate_discharge_summary_pdf(summary_data: dict) -> bytes:
    """
    Generate discharge summary PDF
    
    Args:
        summary_data: Dict with keys: patient_name, summary_text, follow_up, diet_advice, red_flags
    
    Returns:
        PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    # Container for flowables
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=1  # Center
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    elements.append(Paragraph("Hospital Discharge Summary", title_style))
    elements.append(Spacer(1, 12))
    
    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Date:</b> {date_str}", styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Patient Name
    patient_name = summary_data.get('patient_name', 'N/A')
    elements.append(Paragraph(f"<b>Patient Name:</b> {patient_name}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary
    elements.append(Paragraph("Discharge Summary", heading_style))
    summary_text = summary_data.get('summary_text', '').replace('\n', '<br/>')
    elements.append(Paragraph(summary_text, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Follow-up Instructions
    if summary_data.get('follow_up'):
        elements.append(Paragraph("Follow-up Instructions", heading_style))
        follow_up = summary_data['follow_up'].replace('\n', '<br/>')
        elements.append(Paragraph(follow_up, styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Diet Advice
    if summary_data.get('diet_advice'):
        elements.append(Paragraph("Dietary Advice", heading_style))
        diet = summary_data['diet_advice'].replace('\n', '<br/>')
        elements.append(Paragraph(diet, styles['Normal']))
        elements.append(Spacer(1, 20))
    
    # Red Flags
    if summary_data.get('red_flags'):
        elements.append(Paragraph("Red Flag Symptoms", heading_style))
        red_flags = summary_data['red_flags'].replace('\n', '<br/>')
        warning_style = ParagraphStyle(
            'Warning',
            parent=styles['Normal'],
            textColor=colors.red
        )
        elements.append(Paragraph(red_flags, warning_style))
        elements.append(Spacer(1, 20))
    
    # Disclaimer
    elements.append(Spacer(1, 30))
    disclaimer = "<i>This discharge summary is generated for informational purposes and does not replace professional medical advice.</i>"
    elements.append(Paragraph(disclaimer, styles['Normal']))
    
    # Build PDF
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_bill_analysis_pdf(bill_data: dict) -> bytes:
    """
    Generate bill analysis PDF
    
    Args:
        bill_data: Dict with analysis results
    
    Returns:
        PDF bytes
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72,
                           topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1a5490'),
        spaceAfter=30,
        alignment=1
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#2c5aa0'),
        spaceAfter=12,
        spaceBefore=12
    )
    
    # Title
    elements.append(Paragraph("Hospital Bill Analysis Report", title_style))
    elements.append(Spacer(1, 12))
    
    # Date
    date_str = datetime.now().strftime("%B %d, %Y")
    elements.append(Paragraph(f"<b>Analysis Date:</b> {date_str}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Summary
    cghs_comparison = bill_data.get('cghs_comparison', {})
    total_excess = cghs_comparison.get('total_excess', 0)
    
    elements.append(Paragraph("Summary", heading_style))
    elements.append(Paragraph(f"<b>Total Overcharged Amount:</b> ₹{total_excess:.2f}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Overcharged Items
    overcharged = cghs_comparison.get('overcharged', [])
    if overcharged:
        elements.append(Paragraph("Overcharged Items", heading_style))
        
        table_data = [['Item', 'Billed', 'CGHS Rate', 'Excess']]
        for item in overcharged:
            table_data.append([
                item['description'][:40],
                f"₹{item['billed_amount']:.2f}",
                f"₹{item['cghs_rate']:.2f}",
                f"₹{item['excess']:.2f}"
            ])
        
        table = Table(table_data, colWidths=[3*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    # Medicine Analysis
    if bill_data.get('medicine_analysis'):
        elements.append(Paragraph("Medicine Price Analysis", heading_style))
        
        medicine_data = bill_data['medicine_analysis']
        table_data = [['Brand', 'Generic', 'Billed', 'Expected', 'Excess']]
        
        for med in medicine_data:
            table_data.append([
                med['brand_name'][:30],
                med['generic_name'][:30],
                f"₹{med['billed_price']:.2f}",
                f"₹{med['expected_price']:.2f}",
                f"₹{med['excess']:.2f}"
            ])
        
        table = Table(table_data, colWidths=[1.5*inch, 1.5*inch, 1*inch, 1*inch, 1*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c5aa0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 20))
    
    # Disclaimer
    elements.append(Spacer(1, 30))
    disclaimer = "<i>This analysis is for informational purposes only and does not constitute legal or medical advice. Please verify all charges with your hospital.</i>"
    elements.append(Paragraph(disclaimer, styles['Normal']))
    
    doc.build(elements)
    
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
