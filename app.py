"""
Shorecrest Pay Application Automation System
Streamlit Web App - Drag & Drop Stamp Placement

Blue Scarf Solutions - First Client Deliverable
"""

import streamlit as st
import streamlit.components.v1 as components
from streamlit_js_eval import streamlit_js_eval
import datetime
from PIL import Image
import io
import base64
import json

from modules.ocr import extract_text_from_pdf
from modules.parser import parse_invoice
from modules.lookup import lookup_vendor

# Page config
st.set_page_config(
    page_title="Pay Application Processor",
    page_icon="📄",
    layout="wide"
)

# CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * { font-family: 'Inter', sans-serif; }
    
    .main-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1rem 0;
        border-bottom: 2px solid #2563eb;
        margin-bottom: 1.5rem;
    }
    .header-left {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .header-title { font-size: 1.4rem; font-weight: 700; color: #1a1a1a; }
    .header-subtitle { font-size: 0.85rem; color: #64748b; font-weight: 500; }
    .bss-badge {
        display: flex;
        align-items: center;
        gap: 8px;
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
        color: white;
        padding: 6px 14px;
        border-radius: 6px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .bss-badge img { height: 22px; }
    .success-card {
        background: linear-gradient(135deg, #f0fdf4, #dcfce7);
        border: 2px solid #22c55e;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(34, 197, 94, 0.15);
    }
    .success-card h2 { color: #166534; margin-bottom: 0.5rem; }
    .step-indicator {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin-bottom: 1.5rem;
        font-size: 0.85rem;
    }
    .step { 
        padding: 8px 16px; 
        border-radius: 25px; 
        background: #f1f5f9;
        color: #64748b;
        border: 2px solid transparent;
        transition: all 0.2s;
    }
    .step.active { 
        background: linear-gradient(135deg, #1d4ed8, #2563eb); 
        color: white;
        font-weight: 600;
        box-shadow: 0 2px 8px rgba(37, 99, 235, 0.4);
    }
    .step.done {
        background: #dcfce7;
        color: #166534;
        border-color: #22c55e;
    }
    .instructions {
        background: #f8fafc;
        border-left: 3px solid #2563eb;
        padding: 12px 16px;
        margin: 1rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
        color: #475569;
    }
    .tip {
        background: #fefce8;
        border-left: 3px solid #eab308;
        padding: 10px 14px;
        margin: 0.5rem 0;
        border-radius: 0 6px 6px 0;
        font-size: 0.9rem;
    }
    .bss-footer {
        margin-top: 3rem;
        padding: 1.5rem 0;
        border-top: 1px solid #e2e8f0;
        text-align: center;
        color: #64748b;
        font-size: 0.85rem;
    }
    .bss-footer a { color: #2563eb; text-decoration: none; }
    .bss-footer a:hover { text-decoration: underline; }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton > button { 
        border-radius: 8px; 
        padding: 0.75rem 1.5rem; 
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #1d4ed8, #2563eb);
    }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="main-header">
    <div class="header-left">
        <span class="header-title">📄 Pay Application Processor</span>
        <span class="header-subtitle">Shorecrest Construction</span>
    </div>
    <div class="bss-badge">
        🐧 Powered by Blue Scarf Solutions
    </div>
</div>
""", unsafe_allow_html=True)


def show_progress(current_step):
    """Show progress indicator with 4 steps"""
    steps = [
        ("1", "Upload"),
        ("2", "Verify"),
        ("3", "Place Stamp"),
        ("4", "Download")
    ]
    step_map = {'upload': 0, 'verify': 1, 'position': 2, 'generate': 2, 'preview': 2, 'download': 3}
    current_idx = step_map.get(current_step, 0)
    
    html = '<div class="step-indicator">'
    for i, (num, label) in enumerate(steps):
        if i < current_idx:
            cls = "step done"
            icon = "✓"
        elif i == current_idx:
            cls = "step active"
            icon = num
        else:
            cls = "step"
            icon = num
        html += f'<span class="{cls}">{icon} {label}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def process_invoice(pdf_bytes: bytes, filename: str):
    with st.spinner("Reading invoice..."):
        text = extract_text_from_pdf(pdf_bytes=pdf_bytes)
        invoice_data = parse_invoice(text)
        com_id, cost_code, matched_vendor = lookup_vendor(invoice_data.vendor_name)
        if com_id:
            invoice_data.commitment_id = com_id
        if cost_code:
            invoice_data.cost_code = cost_code
        return invoice_data, matched_vendor


def main():
    # Initialize session state
    if 'stage' not in st.session_state:
        st.session_state.stage = 'upload'
    if 'pdf_bytes' not in st.session_state:
        st.session_state.pdf_bytes = None
    if 'stamp_x' not in st.session_state:
        st.session_state.stamp_x = 50
    if 'stamp_y' not in st.session_state:
        st.session_state.stamp_y = 50
    if 'stamp_w' not in st.session_state:
        st.session_state.stamp_w = 140
    if 'stamp_h' not in st.session_state:
        st.session_state.stamp_h = 80
    if 'zoom' not in st.session_state:
        st.session_state.zoom = 1.0
    
    # ========== STAGE 1: UPLOAD ==========
    if st.session_state.stage == 'upload':
        show_progress('upload')
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### 📤 Upload Invoice")
            
            st.markdown("""
            <div class="instructions">
                <strong>What to do:</strong> Upload a subcontractor payment application (PDF).<br>
                The system will automatically extract vendor info, amounts, and match it to your records.
            </div>
            """, unsafe_allow_html=True)
            
            uploaded_file = st.file_uploader(
                "Drop your PDF here or click to browse",
                type=['pdf'],
                help="Accepts AIA G702 payment applications and similar invoice formats"
            )
            
            if uploaded_file:
                st.session_state.pdf_bytes = uploaded_file.read()
                st.session_state.filename = uploaded_file.name
                invoice_data, matched_vendor = process_invoice(
                    st.session_state.pdf_bytes,
                    st.session_state.filename
                )
                st.session_state.invoice_data = invoice_data
                st.session_state.matched_vendor = matched_vendor
                st.session_state.stage = 'verify'
                st.rerun()
    
    # ========== STAGE 2: VERIFY ==========
    elif st.session_state.stage == 'verify':
        show_progress('verify')
        
        from modules.lookup import get_lookup
        
        data = st.session_state.invoice_data
        lookup = get_lookup()
        
        # Get all options from CSV
        all_vendors = sorted([v for v in lookup.list_vendors() if v])
        all_commitment_ids = sorted([str(c) for c in lookup.df['commitment_id'].unique() if c])
        all_cost_codes = sorted([str(c) for c in lookup.df['cost_code'].unique() if c])
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### ✏️ Verify Details")
            
            st.markdown("""
            <div class="instructions">
                <strong>What to do:</strong> Check that the extracted info is correct. 
                Use the dropdowns to fix any fields — just start typing to search.
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"**File:** `{st.session_state.filename}`")
            
            if st.session_state.matched_vendor:
                st.success(f"✓ Vendor matched: **{st.session_state.matched_vendor}**")
            else:
                st.warning("⚠️ Vendor not auto-matched — please select from dropdown")
            
            st.markdown("")
            
            c1, c2 = st.columns(2)
            with c1:
                # Vendor dropdown
                vendor_options = [""] + all_vendors
                default_vendor_idx = 0
                if data.vendor_name and data.vendor_name in vendor_options:
                    default_vendor_idx = vendor_options.index(data.vendor_name)
                elif st.session_state.matched_vendor and st.session_state.matched_vendor in vendor_options:
                    default_vendor_idx = vendor_options.index(st.session_state.matched_vendor)
                
                vendor = st.selectbox(
                    "Vendor Name",
                    options=vendor_options,
                    index=default_vendor_idx,
                    help="Start typing to search"
                )
                
                # Commitment ID
                commitment_options = [""] + all_commitment_ids
                default_commit_idx = 0
                if data.commitment_id and data.commitment_id in commitment_options:
                    default_commit_idx = commitment_options.index(data.commitment_id)
                
                commitment_id = st.selectbox(
                    "Commitment ID",
                    options=commitment_options,
                    index=default_commit_idx
                )
                
                # Cost Code
                cost_code_options = [""] + all_cost_codes
                default_cost_idx = 0
                if data.cost_code and data.cost_code in cost_code_options:
                    default_cost_idx = cost_code_options.index(data.cost_code)
                
                cost_code = st.selectbox(
                    "Cost Code",
                    options=cost_code_options,
                    index=default_cost_idx
                )
            
            with c2:
                amount_str = st.text_input(
                    "Amount Due ($)",
                    value=f"{float(data.amount_due):,.2f}"
                )
                try:
                    amount_due = float(amount_str.replace(",", "").replace("$", ""))
                except:
                    amount_due = 0.0
                
                retainage_str = st.text_input(
                    "Retainage ($)",
                    value=f"{float(data.retainage):,.2f}"
                )
                try:
                    retainage = float(retainage_str.replace(",", "").replace("$", ""))
                except:
                    retainage = 0.0
            
            # Stamp Preview
            st.markdown("---")
            st.markdown("**Your approval stamp will look like this:**")
            preview_date = datetime.datetime.now().strftime("%-m/%-d/%Y")
            
            stamp_preview_html = f"""
            <div style="
                border: 2px solid #333;
                border-radius: 4px;
                padding: 12px 15px;
                background: white;
                font-family: 'Helvetica', sans-serif;
                font-size: 13px;
                line-height: 1.6;
                max-width: 200px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
            ">
                <div><strong>COM:</strong> {commitment_id or '____________'}</div>
                <div><strong>C.C:</strong> {cost_code or '____________'}</div>
                <div><strong>DUE:</strong> ${amount_due:,.2f}</div>
                <div><strong>RET:</strong> ${retainage:,.2f}</div>
                <div><strong>By:</strong> Alan Sar Shalom</div>
                <div><strong>Date:</strong> {preview_date}</div>
            </div>
            """
            st.markdown(stamp_preview_html, unsafe_allow_html=True)
            
            st.markdown("---")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Back", use_container_width=True):
                    st.session_state.stage = 'upload'
                    st.rerun()
            with c2:
                if st.button("Next: Place Stamp →", type="primary", use_container_width=True):
                    st.session_state.final_data = {
                        'vendor': vendor,
                        'commitment_id': commitment_id,
                        'cost_code': cost_code,
                        'amount_due': amount_due,
                        'retainage': retainage,
                    }
                    st.session_state.stage = 'position'
                    st.rerun()
    
    # ========== STAGE 3: POSITION STAMP ==========
    elif st.session_state.stage == 'position':
        show_progress('position')
        
        from modules.stamper import get_pdf_preview, get_pdf_dimensions
        
        st.markdown("### 📍 Place Your Stamp")
        
        st.markdown("""
        <div class="instructions">
            <strong>How to place your stamp:</strong><br>
            1️⃣ <strong>Drag</strong> the blue box to where you want the stamp<br>
            2️⃣ <strong>Resize</strong> by pulling the corner handles (optional)<br>
            3️⃣ <strong>Click "🔄 Lock Position"</strong> to save your placement<br>
            4️⃣ <strong>Click "Apply Stamp"</strong> to finish
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div class="tip">
            ⚠️ <strong>Important:</strong> You must click <strong>"🔄 Lock Position"</strong> after moving the stamp — otherwise your placement won't be saved!
        </div>
        """, unsafe_allow_html=True)
        
        # Get PDF dimensions and generate preview
        pdf_width, pdf_height = get_pdf_dimensions(st.session_state.pdf_bytes)
        zoom = 800 / pdf_width
        st.session_state.zoom = zoom
        
        preview_png, canvas_width, canvas_height = get_pdf_preview(
            st.session_state.pdf_bytes, 
            zoom=zoom
        )
        
        img_b64 = base64.b64encode(preview_png).decode()
        
        init_x = int(st.session_state.stamp_x)
        init_y = int(st.session_state.stamp_y)
        init_w = int(st.session_state.stamp_w)
        init_h = int(st.session_state.stamp_h)
        
        # Drag-and-drop canvas
        canvas_html = f"""
        <style>
            #canvas-container {{ position: relative; display: inline-block; user-select: none; }}
            #pdf-image {{ display: block; border: 1px solid #e2e8f0; border-radius: 4px; }}
            #stamp-box {{
                position: absolute;
                border: 3px solid #2563eb;
                background: rgba(37, 99, 235, 0.15);
                cursor: move;
                box-sizing: border-box;
            }}
            .resize-handle {{
                position: absolute; width: 14px; height: 14px;
                background: #2563eb; border: 2px solid white; border-radius: 2px;
            }}
            .resize-handle.nw {{ top: -7px; left: -7px; cursor: nw-resize; }}
            .resize-handle.ne {{ top: -7px; right: -7px; cursor: ne-resize; }}
            .resize-handle.sw {{ bottom: -7px; left: -7px; cursor: sw-resize; }}
            .resize-handle.se {{ bottom: -7px; right: -7px; cursor: se-resize; }}
            #stamp-label {{
                position: absolute; top: 50%; left: 50%;
                transform: translate(-50%, -50%);
                color: #1d4ed8; font-weight: bold; font-size: 14px;
                pointer-events: none; text-shadow: 1px 1px 2px white;
            }}
            #coords-display {{
                margin-top: 10px; padding: 10px 15px;
                background: #f0f9ff; border-radius: 6px;
                font-family: monospace; font-size: 13px;
            }}
        </style>
        <div id="canvas-container">
            <img id="pdf-image" src="data:image/png;base64,{img_b64}" width="{canvas_width}" height="{canvas_height}">
            <div id="stamp-box" style="left:{init_x}px;top:{init_y}px;width:{init_w}px;height:{init_h}px;">
                <span id="stamp-label">STAMP</span>
                <div class="resize-handle nw" data-resize="nw"></div>
                <div class="resize-handle ne" data-resize="ne"></div>
                <div class="resize-handle sw" data-resize="sw"></div>
                <div class="resize-handle se" data-resize="se"></div>
            </div>
        </div>
        <div id="coords-display">
            📍 Position: (<span id="pos-x">{init_x}</span>, <span id="pos-y">{init_y}</span>) | 
            📐 Size: <span id="size-w">{init_w}</span> × <span id="size-h">{init_h}</span> px
        </div>
        <script>
            const box = document.getElementById('stamp-box');
            let isDragging = false, isResizing = false, resizeDir = '';
            let startX, startY, startLeft, startTop, startWidth, startHeight;
            
            function updatePosition() {{
                const x = Math.round(parseFloat(box.style.left));
                const y = Math.round(parseFloat(box.style.top));
                const w = Math.round(parseFloat(box.style.width));
                const h = Math.round(parseFloat(box.style.height));
                document.getElementById('pos-x').textContent = x;
                document.getElementById('pos-y').textContent = y;
                document.getElementById('size-w').textContent = w;
                document.getElementById('size-h').textContent = h;
                localStorage.setItem('stampPosition', JSON.stringify({{x:x, y:y, w:w, h:h}}));
            }}
            
            localStorage.setItem('stampPosition', JSON.stringify({{x:{init_x}, y:{init_y}, w:{init_w}, h:{init_h}}}));
            
            box.addEventListener('mousedown', function(e) {{
                if (e.target.classList.contains('resize-handle')) {{
                    isResizing = true;
                    resizeDir = e.target.dataset.resize;
                }} else {{ isDragging = true; }}
                startX = e.clientX; startY = e.clientY;
                startLeft = parseFloat(box.style.left); startTop = parseFloat(box.style.top);
                startWidth = parseFloat(box.style.width); startHeight = parseFloat(box.style.height);
                e.preventDefault();
            }});
            
            document.addEventListener('mousemove', function(e) {{
                if (isDragging) {{
                    let newLeft = Math.max(0, Math.min(startLeft + e.clientX - startX, {canvas_width} - parseFloat(box.style.width)));
                    let newTop = Math.max(0, Math.min(startTop + e.clientY - startY, {canvas_height} - parseFloat(box.style.height)));
                    box.style.left = newLeft + 'px'; box.style.top = newTop + 'px';
                    updatePosition();
                }}
                if (isResizing) {{
                    let dx = e.clientX - startX, dy = e.clientY - startY;
                    let newW = startWidth, newH = startHeight, newL = startLeft, newT = startTop;
                    if (resizeDir.includes('e')) newW = Math.max(60, startWidth + dx);
                    if (resizeDir.includes('w')) {{ newW = Math.max(60, startWidth - dx); newL = startLeft + startWidth - newW; }}
                    if (resizeDir.includes('s')) newH = Math.max(40, startHeight + dy);
                    if (resizeDir.includes('n')) {{ newH = Math.max(40, startHeight - dy); newT = startTop + startHeight - newH; }}
                    box.style.width = newW + 'px'; box.style.height = newH + 'px';
                    box.style.left = newL + 'px'; box.style.top = newT + 'px';
                    updatePosition();
                }}
            }});
            
            document.addEventListener('mouseup', function() {{ isDragging = false; isResizing = false; }});
        </script>
        """
        
        components.html(canvas_html, height=canvas_height + 80)
        
        # Read position from localStorage
        position_json = streamlit_js_eval(
            js_expressions="localStorage.getItem('stampPosition')",
            key=f"read_pos_{st.session_state.get('pos_read_key', 0)}"
        )
        
        if position_json:
            try:
                pos = json.loads(position_json)
                st.session_state.stamp_x = pos['x']
                st.session_state.stamp_y = pos['y']
                st.session_state.stamp_w = pos['w']
                st.session_state.stamp_h = pos['h']
            except:
                pass
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("← Back", use_container_width=True):
                st.session_state.stage = 'verify'
                st.rerun()
        with col2:
            if st.button("🔄 Lock Position", use_container_width=True, type="secondary"):
                st.session_state.pos_read_key = st.session_state.get('pos_read_key', 0) + 1
                st.rerun()
        with col3:
            if st.button("✓ Apply Stamp", type="primary", use_container_width=True):
                st.session_state.pos_read_key = st.session_state.get('pos_read_key', 0) + 1
                st.session_state.stage = 'generate'
                st.rerun()
    
    # ========== STAGE 4: GENERATE (loading) ==========
    elif st.session_state.stage == 'generate':
        show_progress('position')
        
        from modules.stamper import stamp_pdf_at_position, get_pdf_preview
        
        with st.spinner("Applying stamp to PDF..."):
            final = st.session_state.final_data
            
            output_bytes, debug_info = stamp_pdf_at_position(
                pdf_bytes=st.session_state.pdf_bytes,
                commitment_id=final['commitment_id'],
                cost_code=final['cost_code'],
                amount_due=final['amount_due'],
                retainage=final['retainage'],
                approver="Alan Sar Shalom",
                canvas_x=st.session_state.stamp_x,
                canvas_y=st.session_state.stamp_y,
                canvas_w=st.session_state.stamp_w,
                canvas_h=st.session_state.stamp_h,
                zoom=st.session_state.zoom,
                debug=True
            )
            
            st.session_state.output_bytes = output_bytes
            st.session_state.debug_info = debug_info
            
            preview_png, _, _ = get_pdf_preview(output_bytes, zoom=st.session_state.zoom)
            st.session_state.preview_png = preview_png
            st.session_state.stage = 'preview'
            st.rerun()
    
    # ========== STAGE 5: PREVIEW ==========
    elif st.session_state.stage == 'preview':
        show_progress('position')
        
        st.markdown("### 👀 Preview")
        
        st.markdown("""
        <div class="instructions">
            <strong>Check the result:</strong> Make sure the stamp is in the right spot and looks correct.
        </div>
        """, unsafe_allow_html=True)
        
        st.image(st.session_state.preview_png, width=800)
        
        st.markdown("---")
        
        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Move Stamp", use_container_width=True):
                st.session_state.stage = 'position'
                st.rerun()
        with c2:
            if st.button("✓ Looks Good!", type="primary", use_container_width=True):
                st.session_state.stage = 'download'
                st.rerun()
    
    # ========== STAGE 6: DOWNLOAD ==========
    elif st.session_state.stage == 'download':
        show_progress('download')
        
        final = st.session_state.final_data
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div class="success-card">
                <h2>✅ Invoice Approved!</h2>
                <p style="margin-top: 0.5rem; color: #166534;">Your stamp has been applied successfully.</p>
            </div>
            """, unsafe_allow_html=True)
            
            vendor_clean = final['vendor'].replace(' ', '_').replace(',', '').replace('/', '-')
            output_filename = f"{vendor_clean}_{datetime.datetime.now().strftime('%B_%Y')}_Approved.pdf"
            
            st.markdown("")
            st.markdown("**Download your stamped invoice:**")
            
            st.download_button(
                "📥 Download PDF",
                st.session_state.output_bytes,
                output_filename,
                "application/pdf",
                use_container_width=True
            )
            
            st.markdown("---")
            st.markdown("**What's next?**")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("← Adjust Stamp", use_container_width=True, help="Go back and reposition the stamp"):
                    st.session_state.stage = 'position'
                    st.rerun()
            with c2:
                if st.button("🔄 Process Another Invoice", type="primary", use_container_width=True):
                    for key in list(st.session_state.keys()):
                        del st.session_state[key]
                    st.rerun()
    
    # Footer on all pages
    st.markdown("""
    <div class="bss-footer">
        Built with 🐧 by <a href="https://bluescarfsolutions.com" target="_blank">Blue Scarf Solutions</a><br>
        <span style="font-size: 0.75rem; color: #94a3b8;">Automation that works while you sleep</span>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
