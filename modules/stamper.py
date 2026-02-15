"""
Stamper Module - Visual coordinates → Drawing coordinates via derotation matrix
Handles rotated PDFs correctly (270° scanned invoices)
"""

import io
from datetime import datetime
from typing import Tuple
import fitz


def stamp_pdf_at_position(
    pdf_bytes: bytes,
    commitment_id: str = "",
    cost_code: str = "",
    amount_due: float = 0.0,
    retainage: float = 0.0,
    approver: str = "Alan Sar Shalom",
    canvas_x: float = 50,
    canvas_y: float = 50,
    canvas_w: float = 140,
    canvas_h: float = 80,
    zoom: float = 1.0,
    debug: bool = False
) -> Tuple[bytes, dict]:
    """Apply approval stamp at visual canvas position.
    
    Uses page.derotation_matrix to transform visual coordinates
    (what the user sees) to drawing coordinates.
    Text is inserted with rotation to appear upright in rotated pages.
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[0]
    
    rotation = page.rotation
    derot = page.derotation_matrix
    
    # Canvas to visual points (divide by zoom)
    visual_x = canvas_x / zoom
    visual_y = canvas_y / zoom
    stamp_w = canvas_w / zoom
    stamp_h = canvas_h / zoom
    
    # Transform all 4 visual corners to drawing coordinates
    corners_visual = [
        fitz.Point(visual_x, visual_y),
        fitz.Point(visual_x + stamp_w, visual_y),
        fitz.Point(visual_x, visual_y + stamp_h),
        fitz.Point(visual_x + stamp_w, visual_y + stamp_h),
    ]
    corners_draw = [c * derot for c in corners_visual]
    
    # Bounding rect in drawing coords
    xs = [c.x for c in corners_draw]
    ys = [c.y for c in corners_draw]
    drawing_rect = fitz.Rect(min(xs), min(ys), max(xs), max(ys))
    
    debug_info = {
        'rotation': rotation,
        'zoom': zoom,
        'visual': {'x': visual_x, 'y': visual_y, 'w': stamp_w, 'h': stamp_h},
        'canvas': {'x': canvas_x, 'y': canvas_y, 'w': canvas_w, 'h': canvas_h},
        'drawing_rect': str(drawing_rect),
        'drawing_size': f"{drawing_rect.width:.1f} x {drawing_rect.height:.1f}",
    }
    
    # Draw white background with dark border (using shape for reliability)
    shape = page.new_shape()
    shape.draw_rect(drawing_rect)
    shape.finish(color=(0.2, 0.2, 0.2), fill=(1, 1, 1), width=1.5)
    shape.commit()
    
    # Build text content
    date = datetime.now().strftime("%-m/%-d/%Y")
    text_content = f"""COM: {commitment_id or '________'}
C.C: {cost_code or '________'}
DUE: ${amount_due:,.2f}
RET: ${retainage:,.2f}
By: {approver}
Date: {date}"""
    
    # For rotated pages, determine text rotation to keep upright
    # Text rotation must MATCH page rotation to appear upright
    text_rotate = 0
    if rotation == 270:
        text_rotate = 270  # Same direction as page
    elif rotation == 90:
        text_rotate = 90
    elif rotation == 180:
        text_rotate = 180
    
    # When text is rotated, the "width" and "height" of the textbox swap roles
    # For 90° or 270° text rotation, textbox is filled along its HEIGHT
    padding = 5
    text_rect = fitz.Rect(
        drawing_rect.x0 + padding,
        drawing_rect.y0 + padding,
        drawing_rect.x1 - padding,
        drawing_rect.y1 - padding
    )
    
    # Calculate font size to fit
    # For 90° rotation: text flows along the rect height, wraps at rect width
    lines = text_content.strip().split('\n')
    num_lines = len(lines)
    longest_line = max(lines, key=len)
    
    if text_rotate in (90, 270):
        # Text flows along height, width becomes line width limit
        available_line_width = text_rect.height - 10  # along height
        available_stack_height = text_rect.width - 10  # perpendicular
    else:
        available_line_width = text_rect.width - 10
        available_stack_height = text_rect.height - 10
    
    # Font size from width constraint (0.5 char width ratio for Helvetica)
    fontsize_w = available_line_width / (len(longest_line) * 0.52)
    # Font size from height constraint (1.3 line height ratio)
    fontsize_h = available_stack_height / (num_lines * 1.25)
    
    fontsize = min(fontsize_w, fontsize_h)
    fontsize = max(5, min(fontsize, 10))  # Clamp 5-10pt
    
    debug_info['text_rotate'] = text_rotate
    debug_info['text_rect'] = str(text_rect)
    debug_info['fontsize'] = round(fontsize, 1)
    debug_info['available_line_width'] = round(available_line_width, 1)
    
    # Insert text with rotation
    rc = page.insert_textbox(
        text_rect,
        text_content,
        fontsize=fontsize,
        fontname="helv",
        color=(0, 0, 0),
        align=fitz.TEXT_ALIGN_LEFT,
        rotate=text_rotate
    )
    
    debug_info['textbox_rc'] = round(rc, 1)  # negative = overflow
    
    output = io.BytesIO()
    doc.save(output)
    doc.close()
    
    return output.getvalue(), debug_info


def get_pdf_preview(pdf_bytes: bytes, page_num: int = 0, zoom: float = 1.0):
    """Render PDF page to PNG at given zoom level."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
    png_bytes = pix.tobytes("png")
    width, height = pix.width, pix.height
    doc.close()
    return png_bytes, width, height


def get_pdf_dimensions(pdf_bytes: bytes, page_num: int = 0) -> Tuple[float, float]:
    """Get visual dimensions of PDF page (accounting for rotation)."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    width = page.rect.width
    height = page.rect.height
    doc.close()
    return width, height


def get_pdf_rotation(pdf_bytes: bytes, page_num: int = 0) -> int:
    """Get rotation of PDF page in degrees."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_num]
    rotation = page.rotation
    doc.close()
    return rotation
