import streamlit as st
import requests
import io
import os
import time
from PyPDF2 import PdfReader
import tempfile
from dotenv import load_dotenv
import json
import pandas as pd
import re

# Load environment variables from .env file
load_dotenv()

def generate_pdf(response_draft, review):
    """Generate a PDF document from the RFP response and review"""
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from io import BytesIO
    
    # Create a BytesIO buffer to receive the PDF data
    buffer = BytesIO()
    
    # Create the PDF document
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Create custom styles
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12
    )
    
    heading2_style = ParagraphStyle(
        'Heading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=10
    )
    
    normal_style = ParagraphStyle(
        'Normal',
        parent=styles['Normal'],
        fontSize=11,
        spaceAfter=8
    )
    
    # Build the document content
    content = []
    
    # Add title
    content.append(Paragraph("RFP Response Draft", title_style))
    content.append(Spacer(1, 12))
    
    # Basic markdown to PDF conversion (simplified)
    lines = response_draft.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            content.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            content.append(Paragraph(line[3:], heading2_style))
        elif line.startswith('### '):
            content.append(Paragraph(line[4:], heading2_style))
        elif line.startswith('- ') or line.startswith('* '):
            content.append(Paragraph(f"• {line[2:]}", normal_style))
        else:
            content.append(Paragraph(line, normal_style))
    
    # Add review section
    content.append(Spacer(1, 20))
    content.append(Paragraph("Quality Review", title_style))
    content.append(Spacer(1, 12))
    
    # Add review content
    lines = review.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            content.append(Paragraph(line[2:], title_style))
        elif line.startswith('## '):
            content.append(Paragraph(line[3:], heading2_style))
        elif line.startswith('### '):
            content.append(Paragraph(line[4:], heading2_style))
        elif line.startswith('- ') or line.startswith('* '):
            content.append(Paragraph(f"• {line[2:]}", normal_style))
        else:
            content.append(Paragraph(line, normal_style))
    
    # Build the PDF
    doc.build(content)
    buffer.seek(0)
    return buffer

def generate_docx(response_draft, review):
    """Generate a Word document from the RFP response and review"""
    from docx import Document
    from docx.shared import Pt, RGBColor
    from io import BytesIO
    
    # Create a new Document
    doc = Document()
    
    # Add a title
    title = doc.add_heading("RFP Response Draft", level=1)
    title_format = title.runs[0].font
    title_format.size = Pt(18)
    
    # Process the response draft content
    lines = response_draft.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            heading = doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            heading = doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            heading = doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph()
            p.add_run("• " + line[2:])
            p.style = 'List Bullet'
        else:
            p = doc.add_paragraph(line)
    
    # Add a page break before the review section
    doc.add_page_break()
    
    # Add the review section title
    review_title = doc.add_heading("Quality Review", level=1)
    
    # Process the review content
    lines = review.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        if line.startswith('# '):
            heading = doc.add_heading(line[2:], level=1)
        elif line.startswith('## '):
            heading = doc.add_heading(line[3:], level=2)
        elif line.startswith('### '):
            heading = doc.add_heading(line[4:], level=3)
        elif line.startswith('- ') or line.startswith('* '):
            p = doc.add_paragraph()
            p.add_run("• " + line[2:])
            p.style = 'List Bullet'
        else:
            p = doc.add_paragraph(line)
    
    # Save the document to a BytesIO buffer
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

# Simple function to convert markdown to HTML without external dependencies
def simple_md_to_html(md_text):
    """Convert basic markdown to HTML without external dependencies"""
    # Replace headers
    html = md_text.replace("\n# ", "\n<h1>").replace("\n## ", "\n<h2>").replace("\n### ", "\n<h3>")
    html = html.replace("\n</h1>", "</h1>\n").replace("\n</h2>", "</h2>\n").replace("\n</h3>", "</h3>\n")
    
    # Replace lists
    html = html.replace("\n- ", "\n<li>").replace("\n* ", "\n<li>")
    
    # Replace bold and italic
    html = html.replace("**", "<strong>").replace("__", "<strong>")
    html = html.replace("*", "<em>").replace("_", "<em>")
    
    # Replace paragraphs
    paragraphs = html.split("\n\n")
    html = "\n".join([f"<p>{p}</p>" if not (p.startswith("<h") or p.startswith("<li>")) else p for p in paragraphs])
    
    # Replace list items with proper HTML
    html = html.replace("\n<li>", "</li>\n<li>")
    html = html.replace("<li>", "<ul><li>", 1).replace("</li>\n", "</li></ul>\n", 1)
    
    return html

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "rfpdriteam2025":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated
    if st.session_state.get("password_correct", False):
        return True

    # Show input for password
    st.markdown("""
    <style>
    .password-container {
        background-color: #f8f9fa;
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        max-width: 500px;
        margin: 100px auto;
        text-align: center;
    }
    </style>
    <div class="password-container">
        <h1>RFP Response Assistant</h1>
        <h3>Restricted Access</h3>
        <p>This tool is only available to authorized team members.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create password input field
    st.text_input(
        "Enter the access password", 
        type="password", 
        on_change=password_entered, 
        key="password"
    )
    return False

# Now check if the password is correct
if not check_password():
    st.stop()  # Stop execution if password is incorrect

# Configure the Streamlit page
st.set_page_config(
    page_title="RFP Response Assistant",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Get API key from environment variable or Streamlit secrets
def get_api_key():
    # First try to get from Streamlit secrets (when deployed)
    if 'ANTHROPIC_API_KEY' in st.secrets:
        return st.secrets['ANTHROPIC_API_KEY']
    # Then try to get from environment variables (local development)
    elif os.getenv('ANTHROPIC_API_KEY'):
        return os.getenv('ANTHROPIC_API_KEY')
    else:
        st.error("API key not found. Please set it in .env file or Streamlit secrets.")
        st.stop()

# Initialize API key
api_key = get_api_key()

# Updated Anthropic API function for Claude 3 models using Messages API
def call_anthropic_api(prompt, max_tokens=2000, temperature=0, system_prompt=None):
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    messages = [{"role": "user", "content": prompt}]
    
    data = {
        "model": "claude-3-haiku-20240307",  # Using Claude 3 Haiku which is fast and reliable
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": messages
    }
    
    # Add system prompt if provided
    if system_prompt:
        data["system"] = system_prompt
    
    response = requests.post(
        "https://api.anthropic.com/v1/messages", 
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Error from Anthropic API: {response.text}")
    
    # Extract the response text from the messages API format
    response_json = response.json()
    return response_json["content"][0]["text"]

# Enhanced CSS 
st.markdown("""
<style>
    /* Modern UI Theme */
    .main {
        background-color: #f8f9fa;
        background-image: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Header Styling */
    h1 {
        color: #1e3a8a;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #4f46e5;
        display: inline-block;
    }
    h2 {
        color: #1e40af;
        font-weight: 600;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
    }
    h3 {
        color: #1e3a8a;
        font-weight: 600;
        margin-top: 1.25rem;
    }
    
    /* Button Styling */
    .stButton>button {
        background-color: #4f46e5;
        color: white;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        border: none;
        font-size: 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(79, 70, 229, 0.25);
    }
    .stButton>button:hover {
        background-color: #4338ca;
        box-shadow: 0 6px 10px rgba(79, 70, 229, 0.3);
        transform: translateY(-2px);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    
    /* Info Boxes */
    .info-box {
        background-color: #e0f2fe;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #0ea5e9;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .success-box {
        background-color: #dcfce7;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #10b981;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .warning-box {
        background-color: #fef9c3;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 5px solid #eab308;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* Agent Cards */
    .agent-card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        border-top: 4px solid #4f46e5;
        transition: all 0.3s ease;
    }
    .agent-card:hover {
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        transform: translateY(-5px);
    }
    .agent-header {
        font-weight: 700;
        color: #1e40af;
        margin-bottom: 0.5rem;
        font-size: 1.25rem;
        display: flex;
        align-items: center;
    }
    .agent-header svg {
        margin-right: 0.5rem;
    }
    .agent-status {
        font-style: italic;
        color: #6b7280;
        margin-bottom: 1rem;
    }
    
    /* Tables and Data Display */
    .dataframe {
        border-collapse: collapse;
        width: 100%;
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .dataframe th {
        background-color: #4f46e5;
        color: white;
        text-align: left;
        padding: 12px;
    }
    .dataframe td {
        padding: 10px 12px;
        border-bottom: 1px solid #e5e7eb;
    }
    .dataframe tr:nth-child(even) {
        background-color: #f9fafb;
    }
    .dataframe tr:hover {
        background-color: #f3f4f6;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f1f5f9;
    }
    .css-1544g2n {
        padding: 2rem 1rem;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5 !important;
        color: white !important;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background-color: #4f46e5;
    }
    
    /* File uploader */
    .stFileUploader > div > div {
        border: 2px dashed #4f46e5;
        border-radius: 10px;
        padding: 20px;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #059669;
    }
    .stDownloadButton > button:hover {
        background-color: #047857;
    }
    
    /* Card-like sections */
    .card {
        background-color: white;
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    
    /* JSON formatting for requirements */
    .json-key {
        color: #0284c7;
        font-weight: 600;
    }
    .json-value {
        color: #4b5563;
    }
    .json-list-item {
        margin-left: 20px;
        padding: 6px 0;
        border-bottom: 1px dashed #e5e7eb;
    }
    .json-list-item:last-child {
        border-bottom: none;
    }
</style>
""", unsafe_allow_html=True)

# Title and introduction
st.title("🤖 RFP Response Assistant")
st.subheader("Multi-Agent System for Professional Services")

# Sidebar with explanation
with st.sidebar:
    st.header("Multi-Agent System")
    st.markdown("""
    This system uses four specialized AI agents working together to automate RFP responses:
    
    1. **Document Parser Agent**
       - Analyzes RFP documents
       - Extracts key requirements and structure
    
    2. **Knowledge Retrieval Agent**
       - Searches company knowledge base
       - Identifies relevant experience and capabilities
    
    3. **Response Generator Agent**
       - Creates tailored content for each section
       - Aligns responses with requirements
    
    4. **Quality Control Agent**
       - Reviews for completeness and compliance
       - Identifies areas needing human expertise
    """)
    
    st.divider()
    
    # Add company branding
    st.markdown("### Powered by")
    st.image("https://via.placeholder.com/200x60.png?text=YourCompany", width=200)
    
    st.caption("© 2025 Your Company Name")

# Main content area
st.markdown("---")

# File uploader with better styling
st.markdown('<div class="info-box">', unsafe_allow_html=True)
st.subheader("📄 Step 1: Upload RFP Document")
uploaded_file = st.file_uploader("Upload RFP Document (PDF)", type=["pdf"])
st.markdown("</div>", unsafe_allow_html=True)

# Initialize session state for tracking progress and results
if 'rfp_text' not in st.session_state:
    st.session_state.rfp_text = None
if 'requirements' not in st.session_state:
    st.session_state.requirements = None
if 'knowledge' not in st.session_state:
    st.session_state.knowledge = None
if 'response_draft' not in st.session_state:
    st.session_state.response_draft = None
if 'review' not in st.session_state:
    st.session_state.review = None
if 'processing_complete' not in st.session_state:
    st.session_state.processing_complete = False

# Extract text from uploaded document
if uploaded_file is not None:
    # Extract text only if we haven't done it yet
    if st.session_state.rfp_text is None:
        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name
        
        # Extract text from the PDF
        with st.spinner("Extracting text from PDF..."):
            pdf_reader = PdfReader(tmp_path)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text()
            
            os.unlink(tmp_path)  # Remove the temporary file
            
        st.session_state.rfp_text = text
        
        # Show confirmation
        st.success(f"Successfully extracted {len(text)} characters from {uploaded_file.name}")

# Process RFP button - when clicked, start the process
if st.session_state.rfp_text is not None and not st.session_state.processing_complete:
    if st.button("Start Multi-Agent Process", key="start_process"):
        # Display progress for Document Parser Agent
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown('<div class="agent-header">🔍 Document Parser Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Analyzing RFP document and extracting key requirements...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Extracting structured requirements..."):
            # Create prompt for Document Parser Agent
            parser_prompt = f"""You are a Document Parser Agent specialized in analyzing RFP documents. 
            Extract the following information from this RFP:
            1. Key requirements and deliverables
            2. Compliance needs
            3. Deadlines
            4. Evaluation criteria
            5. Required sections for the response
            
            Format your response as JSON with these sections as keys.
            
            RFP content:
            {st.session_state.rfp_text[:15000]}  # Limit content to avoid token limits
            """
            
            # Call Anthropic API with system prompt
            parser_system_prompt = "You are a Document Parser Agent that extracts structured information from RFP documents."
            parser_response = call_anthropic_api(
                parser_prompt, 
                max_tokens=2000, 
                temperature=0,
                system_prompt=parser_system_prompt
            )
            
            # Try to extract JSON from the response
            try:
                start_idx = parser_response.find('{')
                end_idx = parser_response.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = parser_response[start_idx:end_idx]
                    st.session_state.requirements = json.loads(json_str)
                else:
                    st.session_state.requirements = {"error": "Could not extract proper JSON format from response"}
            except Exception as e:
                st.session_state.requirements = {"error": f"Error parsing response: {str(e)}", "raw_response": parser_response}
        
        st.success("✅ Requirements successfully extracted!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display progress for Knowledge Retrieval Agent
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown('<div class="agent-header">🧠 Knowledge Retrieval Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Searching company knowledge base for relevant information...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Retrieving relevant knowledge and past projects..."):
            # Create prompt for Knowledge Retrieval Agent
            knowledge_prompt = f"""Given these RFP requirements, provide relevant information that should be included in our response:
            
            {str(st.session_state.requirements)}
            
            Include:
            1. Suggested past projects that demonstrate relevant experience
            2. Key team members who should be mentioned
            3. Standard service descriptions that match the requirements
            4. Relevant compliance certifications and credentials
            
            Format as a structured list of recommendations.
            """
            
            # Call Anthropic API with system prompt
            knowledge_system_prompt = "You are a Knowledge Retrieval Agent for a professional services firm in Australia. You find relevant information from the company's knowledge base."
            st.session_state.knowledge = call_anthropic_api(
                knowledge_prompt, 
                max_tokens=2000, 
                temperature=0.2,
                system_prompt=knowledge_system_prompt
            )
        
        st.success("✅ Knowledge successfully retrieved!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display progress for Response Generator Agent
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown('<div class="agent-header">✍️ Response Generator Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Creating draft response sections based on requirements and knowledge...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Generating comprehensive response draft..."):
            # Create prompt for Response Generator Agent
            response_prompt = f"""Create draft responses for an RFP based on these requirements and available knowledge:
            
            RFP Requirements:
            {str(st.session_state.requirements)}
            
            Available Knowledge:
            {st.session_state.knowledge}
            
            Generate professional, compelling draft responses for key sections of the RFP.
            Format each section with a clear heading and concise, value-focused content.
            Use markdown formatting for better readability.
            """
            
            # Call Anthropic API with system prompt
            response_system_prompt = "You are a Response Generator Agent for an Australian professional services firm. You create professional RFP response content."
            st.session_state.response_draft = call_anthropic_api(
                response_prompt, 
                max_tokens=3500, 
                temperature=0.4,
                system_prompt=response_system_prompt
            )
        
        st.success("✅ Response draft successfully generated!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Display progress for Quality Control Agent
        st.markdown('<div class="agent-card">', unsafe_allow_html=True)
        st.markdown('<div class="agent-header">🔍 Quality Control Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Reviewing generated response for completeness and compliance...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Performing comprehensive quality review..."):
            # Create prompt for Quality Control Agent
            review_prompt = f"""Review this draft RFP response against the requirements and provide feedback:
            
            Draft Response:
            {st.session_state.response_draft}
            
            RFP Requirements:
            {str(st.session_state.requirements)}
            
            Provide feedback on:
            1. Completeness - Are all requirements addressed?
            2. Compliance - Does it meet all compliance needs?
            3. Consistency - Is the response consistent throughout?
            4. Areas for improvement
            5. Sections requiring human expert review
            
            Format your response in markdown with clear sections.
            """
            
            # Call Anthropic API with system prompt
            review_system_prompt = "You are a Quality Control Agent that reviews RFP responses for completeness, compliance, and quality."
            st.session_state.review = call_anthropic_api(
                review_prompt, 
                max_tokens=2000, 
                temperature=0,
                system_prompt=review_system_prompt
            )
        
        st.success("✅ Quality review successfully completed!")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Mark processing as complete
        st.session_state.processing_complete = True
        
        # Force page refresh to show results
        st.rerun()

# Display results if processing is complete
if st.session_state.processing_complete:
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.subheader("✅ RFP Processing Complete!")
    st.markdown("All agents have successfully completed their tasks. Review the outputs below and download the complete response when you're ready.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    # Create tabs for different outputs
    tab1, tab2, tab3, tab4 = st.tabs(["📋 Requirements", "📚 Knowledge", "📝 Response Draft", "🔍 Quality Review"])
    
    with tab1:
        st.subheader("Extracted Requirements")
        if isinstance(st.session_state.requirements, dict):
            if "error" in st.session_state.requirements:
                st.error(st.session_state.requirements["error"])
                if "raw_response" in st.session_state.requirements:
                    st.text(st.session_state.requirements["raw_response"])
            else:
                # Create a better display for each requirements section
                if "Key_Requirements_And_Deliverables" in st.session_state.requirements:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### 📋 Key Requirements and Deliverables")
                    st.markdown("*The core requirements that must be addressed in your response:*")
                    
                    # Display in a more readable format
                    req_data = st.session_state.requirements["Key_Requirements_And_Deliverables"]
                    
                    if isinstance(req_data, dict):
                        for category, items in req_data.items():
                            # Format category name nicely
                            category_name = category.replace('_', ' ').title()
                            st.markdown(f'<h4 class="json-key">{category_name}</h4>', unsafe_allow_html=True)
                            
                            # Display items as a clean list
                            if isinstance(items, list):
                                for item in items:
                                    st.markdown(f'<div class="json-list-item">{item}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="json-value">{items}</div>', unsafe_allow_html=True)
                            st.markdown("---")
                    else:
                        st.markdown(req_data)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if "Compliance_Needs" in st.session_state.requirements:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### ⚖️ Compliance Requirements")
                    st.markdown("*Mandatory compliance aspects that must be addressed:*")
                    
                    comp_data = st.session_state.requirements["Compliance_Needs"]
                    if isinstance(comp_data, dict):
                        for category, items in comp_data.items():
                            # Format category name nicely
                            category_name = category.replace('_', ' ').title()
                            st.markdown(f'<h4 class="json-key">{category_name}</h4>', unsafe_allow_html=True)
                            
                            # Display items as a clean list
                            if isinstance(items, list):
                                for item in items:
                                    st.markdown(f'<div class="json-list-item">{item}</div>', unsafe_allow_html=True)
                            else:
                                st.markdown(f'<div class="json-value">{items}</div>', unsafe_allow_html=True)
                            st.markdown("---")
                    else:
                        st.markdown(comp_data)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if "Deadlines" in st.session_state.requirements:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### ⏱️ Critical Deadlines")
                    st.markdown("*Important dates and timeline requirements:*")
                    
                    deadline_data = st.session_state.requirements["Deadlines"]
                    if isinstance(deadline_data, dict):
                        # Create a clean table for deadlines
                        deadlines_df = pd.DataFrame({
                            "Milestone": list(deadline_data.keys()),
                            "Date": list(deadline_data.values())
                        })
                        deadlines_df["Milestone"] = deadlines_df["Milestone"].apply(lambda x: x.replace('_', ' ').title())
                        
                        # Display as a styled table
                        st.dataframe(deadlines_df, use_container_width=True)
                    else:
                        st.markdown(deadline_data)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if "Evaluation_Criteria" in st.session_state.requirements:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### 🔍 Evaluation Criteria")
                    st.markdown("*How your proposal will be evaluated:*")
                    
                    eval_data = st.session_state.requirements["Evaluation_Criteria"]
                    if isinstance(eval_data, dict):
                        # Create a better visualization for evaluation criteria
                        criteria = list(eval_data.keys())
                        weights = list(eval_data.values())
                        
                        # Clean up criteria names
                        criteria = [c.replace('_', ' ').replace('-', ' ').title() for c in criteria]
                        
                        # Convert percentage strings to numbers if possible
                        try:
                            weights_numeric = [int(w.replace('%', '')) for w in weights]
                            
                            # Create a dataframe
                            eval_df = pd.DataFrame({
                                "Criterion": criteria,
                                "Weight": weights
                            })
                            
                            # Display as a styled table
                            st.dataframe(eval_df, use_container_width=True)
                            
                            # Add a chart
                            st.markdown("#### Weight Distribution")
                            chart_data = pd.DataFrame({
                                "Criterion": criteria,
                                "Weight": weights_numeric
                            })
                            st.bar_chart(chart_data.set_index("Criterion"), height=300)
                        except:
                            # If conversion fails, just display as text
                            for i, (criterion, weight) in enumerate(zip(criteria, weights)):
                                st.markdown(f"**{criterion}**: {weight}")
                    else:
                        st.markdown(eval_data)
                    st.markdown('</div>', unsafe_allow_html=True)
                
                if "Required_Sections_For_The_Response" in st.session_state.requirements:
                    st.markdown('<div class="card">', unsafe_allow_html=True)
                    st.markdown("### 📑 Required Response Sections")
                    st.markdown("*Sections that must be included in your proposal:*")
                    
                    sections_data = st.session_state.requirements["Required_Sections_For_The_Response"]
                    if isinstance(sections_data, list):
                        # Create a table for required sections
                        sections_df = pd.DataFrame({
                            "Section Number": range(1, len(sections_data) + 1),
                            "Section Name": sections_data
                        })
                        st.dataframe(sections_df, use_container_width=True)
                    else:
                        st.markdown(sections_data)
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.markdown(str(st.session_state.requirements))
    
    with tab2:
        st.subheader("Relevant Knowledge")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(st.session_state.knowledge)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab3:
        st.subheader("Generated Response Draft")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(st.session_state.response_draft)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with tab4:
        st.subheader("Quality Review")
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown(st.session_state.review)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Create downloads section
    st.markdown("### Export Options")
    
    # Create columns for different download formats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Create downloadable markdown response
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Markdown Format")
        md_buffer = io.BytesIO()
        response_text = f"""# RFP Response Draft

{st.session_state.response_draft}

## Quality Review
{st.session_state.review}
"""
        md_buffer.write(response_text.encode())
        md_buffer.seek(0)
        
        st.download_button(
            label="📄 Download as Markdown",
            data=md_buffer,
            file_name="rfp_response_draft.md",
            mime="text/markdown"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        # Create downloadable HTML response for better formatting (without markdown library)
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("HTML Format")
        
        # Convert markdown to HTML using our simple converter
        response_html = simple_md_to_html(st.session_state.response_draft)
        review_html = simple_md_to_html(st.session_state.review)
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>RFP Response</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                h1, h2, h3 {{ color: #1e3a8a; }}
                h1 {{ border-bottom: 2px solid #4f46e5; padding-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #4f46e5; color: white; }}
                tr:hover {{ background-color: #f5f5f5; }}
                .section {{ background-color: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            </style>
        </head>
        <body>
            <h1>RFP Response Draft</h1>
            <div class="section">
                {response_html}
            </div>
            
            <h2>Quality Review</h2>
            <div class="section">
                {review_html}
            </div>
        </body>
        </html>
        """
        
        html_buffer = io.BytesIO()
        html_buffer.write(html_content.encode())
        html_buffer.seek(0)
        
        st.download_button(
            label="📄 Download as HTML",
            data=html_buffer,
            file_name="rfp_response.html",
            mime="text/html"
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col3:
        # Create downloadable Word document
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Word Document")
        
        try:
            docx_buffer = generate_docx(st.session_state.response_draft, st.session_state.review)
            
            st.download_button(
                label="📝 Download as Word",
                data=docx_buffer,
                file_name="rfp_response.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        except Exception as e:
            st.error(f"Error generating Word document: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col4:
        # Create downloadable PDF document
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("PDF Document")
        
        try:
            pdf_buffer = generate_pdf(st.session_state.response_draft, st.session_state.review)
            
            st.download_button(
                label="📑 Download as PDF",
                data=pdf_buffer,
                file_name="rfp_response.pdf",
                mime="application/pdf"
            )
        except Exception as e:
            st.error(f"Error generating PDF: {str(e)}")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Create a summary metrics section
    st.markdown("### Response Summary")
    
    # Create metrics for proposal stats
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Count requirements
        req_count = 0
        if isinstance(st.session_state.requirements, dict) and "Key_Requirements_And_Deliverables" in st.session_state.requirements:
            req_data = st.session_state.requirements["Key_Requirements_And_Deliverables"]
            if isinstance(req_data, dict):
                for category, items in req_data.items():
                    if isinstance(items, list):
                        req_count += len(items)
                    else:
                        req_count += 1
        
        st.metric("Requirements Identified", req_count)
    
    with col2:
        # Estimate response completeness
        completeness = "N/A"
        if st.session_state.review:
            # Look for percentages in the review text
            percentages = re.findall(r'(\d+)%', st.session_state.review)
            if percentages:
                try:
                    # Use the first percentage found as completeness
                    completeness = f"{percentages[0]}%"
                except:
                    pass
        
        st.metric("Response Completeness", completeness)
    
    with col3:
        # Count sections in response
        section_count = 0
        if st.session_state.response_draft:
            # Count markdown headings as sections
            section_count = st.session_state.response_draft.count('\n#')
        
        st.metric("Response Sections", section_count)
    
    with col4:
        # Estimate time saved
        # Assume 30 minutes per requirement for manual processing
        time_saved = req_count * 30  # minutes
        if time_saved > 60:
            time_saved_str = f"{time_saved // 60}h {time_saved % 60}m"
        else:
            time_saved_str = f"{time_saved}m"
        
        st.metric("Estimated Time Saved", time_saved_str)
    
    # Additional options
    st.markdown("### Next Steps")
    st.info("You can now review and refine the generated response before submitting.")
    
    if st.button("Start New RFP", key="reset"):
        # Reset all session state
        st.session_state.rfp_text = None
        st.session_state.requirements = None
        st.session_state.knowledge = None
        st.session_state.response_draft = None
        st.session_state.review = None
        st.session_state.processing_complete = False
        
        # Force page refresh
        st.rerun()

# Display instructions if no file is uploaded
if st.session_state.rfp_text is None and not st.session_state.processing_complete:
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.info("👆 Upload an RFP document to begin the automated response process.")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("""
    ## How This Multi-Agent System Works
    
    This demo showcases how AI agents can collaborate to automate complex tasks like RFP response preparation:
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### 🔍 Document Parser Agent
        - Analyzes RFP documents
        - Extracts key requirements and structure
        - Identifies deadlines and evaluation criteria
        
        ### 🧠 Knowledge Retrieval Agent
        - Searches company knowledge base
        - Finds relevant past projects and experience
        - Identifies suitable team members and qualifications
        """)
    
    with col2:
        st.markdown("""
        ### ✍️ Response Generator Agent
        - Creates tailored content for each section
        - Aligns proposal with requirements
        - Formats response professionally
        
        ### 🔍 Quality Control Agent
        - Reviews for completeness and compliance
        - Identifies gaps and improvement areas
        - Highlights sections needing human expertise
        """)
    
    st.markdown("---")
    
    st.markdown("""
    ### Benefits for Professional Services
    
    - **⏱️ Time Savings**: Reduce RFP response time by 40-60%
    - **⚖️ Consistency**: Ensure all requirements are addressed
    - **🔄 Knowledge Reuse**: Leverage past successful proposals
    - **📈 Win Rate**: Improve proposal quality and compliance
    - **🤝 Collaboration**: Enable teams to focus on high-value contributions
    """)
