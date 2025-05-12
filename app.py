# Replace the API key loading portion of your code with this:

import streamlit as st
import anthropic
import pandas as pd
import io
import os
import time
from PyPDF2 import PdfReader
import tempfile
from dotenv import load_dotenv
import json

# Try to load from .env file for local development
load_dotenv()

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

# Initialize Anthropic client with secure API key retrieval
api_key = get_api_key()
# Ensure compatibility with different Anthropic package versions
try:
    client = anthropic.Anthropic(api_key=api_key)
except TypeError:
    # Fall back to older initialization method if needed
    client = anthropic.Client(api_key=api_key)

# Password protection
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "rfpteamDRI2025":
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

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Configure the Streamlit page
st.set_page_config(
    page_title="RFP Response Assistant",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for a better looking UI
st.markdown("""
<style>
    .main {
        background-color: #f5f7f9;
    }
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .css-18e3th9 {
        padding-top: 2rem;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 24px;
        border-radius: 8px;
        border: none;
        font-size: 16px;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #45a049;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .css-1d391kg {
        padding: 3rem 1rem;
    }
    h1 {
        color: #2e4057;
    }
    h2 {
        color: #2e4057;
        margin-top: 2rem;
    }
    h3 {
        color: #2e4057;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #2196F3;
    }
    .success-box {
        background-color: #e8f5e9;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #4CAF50;
    }
    .warning-box {
        background-color: #fff8e1;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        border-left: 5px solid #FFC107;
    }
    .agent-header {
        font-weight: bold;
        color: #1976D2;
        margin-bottom: 5px;
    }
    .agent-status {
        font-style: italic;
        color: #546e7a;
        margin-bottom: 15px;
    }
    .step-counter {
        background-color: #2e4057;
        color: white;
        border-radius: 50%;
        width: 30px;
        height: 30px;
        text-align: center;
        line-height: 30px;
        display: inline-block;
        margin-right: 10px;
    }
    .highlight {
        background-color: #ffff99;
        padding: 2px 5px;
        border-radius: 3px;
    }
    .requirement {
        background-color: #e3f2fd;
        padding: 10px;
        border-radius: 5px;
        margin: 5px 0;
    }
    .compliant {
        color: green;
    }
    .non-compliant {
        color: red;
    }
    .response-section {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# Title and introduction
col1, col2 = st.columns([5, 1])
with col1:
    st.title("🤖 RFP Response Assistant")
    st.subheader("Multi-Agent System for Professional Services")

with col2:
    st.image("https://via.placeholder.com/100x100.png?text=Logo", width=100)

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "rfp_content" not in st.session_state:
    st.session_state.rfp_content = ""
if "requirements" not in st.session_state:
    st.session_state.requirements = None
if "knowledge" not in st.session_state:
    st.session_state.knowledge = None
if "response_draft" not in st.session_state:
    st.session_state.response_draft = None
if "review" not in st.session_state:
    st.session_state.review = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "step_complete" not in st.session_state:
    st.session_state.step_complete = [False, False, False, False]
if "processing" not in st.session_state:
    st.session_state.processing = False

# Function for Document Parser Agent
def parse_rfp_document(content):
    prompt = f"""You are a Document Parser Agent specialized in analyzing RFP documents. 
    Extract the following information from this RFP:
    1. Key requirements and deliverables
    2. Compliance needs
    3. Deadlines
    4. Evaluation criteria
    5. Required sections for the response
    
    Format your response as JSON with these sections as keys.
    
    RFP content:
    {content[:15000]}  # Limit content to avoid token limits
    """
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2000,
        temperature=0,
        system="You are a Document Parser Agent that extracts structured information from RFP documents.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    try:
        # Try to extract JSON from the response
        response_text = response.content[0].text
        # Look for JSON content
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}') + 1
        if start_idx >= 0 and end_idx > start_idx:
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        return {"error": "Could not extract proper JSON format from response"}
    except Exception as e:
        return {"error": f"Error parsing response: {str(e)}", "raw_response": response.content[0].text}

# Function for Knowledge Retrieval Agent
def retrieve_relevant_knowledge(requirements):
    prompt = f"""You are a Knowledge Retrieval Agent for a professional services firm in Australia.
    Given these RFP requirements, provide relevant information that should be included in our response:
    
    {requirements}
    
    Include:
    1. Suggested past projects that demonstrate relevant experience
    2. Key team members who should be mentioned
    3. Standard service descriptions that match the requirements
    4. Relevant compliance certifications and credentials
    
    Format as a structured list of recommendations.
    """
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2000,
        temperature=0.2,
        system="You are a Knowledge Retrieval Agent that finds relevant information from a company's knowledge base.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

# Function for Response Generator Agent
def generate_response_sections(requirements, knowledge):
    prompt = f"""You are a Response Generator Agent for an Australian professional services firm.
    Create draft responses for an RFP based on these requirements and available knowledge:
    
    RFP Requirements:
    {requirements}
    
    Available Knowledge:
    {knowledge}
    
    Generate professional, compelling draft responses for key sections of the RFP.
    Format each section with a clear heading and concise, value-focused content.
    Use markdown formatting for better readability.
    """
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=3500,
        temperature=0.4,
        system="You are a Response Generator Agent that creates professional RFP response content.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

# Function for Quality Control Agent
def review_response(response_content, requirements):
    prompt = f"""You are a Quality Control Agent for RFP responses.
    Review this draft RFP response against the requirements and provide feedback:
    
    Draft Response:
    {response_content}
    
    RFP Requirements:
    {requirements}
    
    Provide feedback on:
    1. Completeness - Are all requirements addressed?
    2. Compliance - Does it meet all compliance needs?
    3. Consistency - Is the response consistent throughout?
    4. Areas for improvement
    5. Sections requiring human expert review
    
    Format your response in markdown with clear sections.
    """
    
    response = client.messages.create(
        model="claude-3-7-sonnet-20250219",
        max_tokens=2000,
        temperature=0,
        system="You are a Quality Control Agent that reviews RFP responses for completeness, compliance, and quality.",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.content[0].text

# Sidebar with explanation and progress tracking
with st.sidebar:
    st.header("Multi-Agent System")
    st.markdown("""
    This system uses four specialized AI agents working together to automate RFP responses:
    """)
    
    # Progress indicators for each agent
    st.subheader("Agent Status")
    
    # Document Parser Agent status
    if st.session_state.step_complete[0]:
        st.markdown("✅ **Document Parser Agent**")
    elif st.session_state.current_step == 0 and st.session_state.processing:
        st.markdown("🔄 **Document Parser Agent** *(Working...)*")
    else:
        st.markdown("⏳ **Document Parser Agent**")
    
    # Knowledge Retrieval Agent status
    if st.session_state.step_complete[1]:
        st.markdown("✅ **Knowledge Retrieval Agent**")
    elif st.session_state.current_step == 1 and st.session_state.processing:
        st.markdown("🔄 **Knowledge Retrieval Agent** *(Working...)*")
    else:
        st.markdown("⏳ **Knowledge Retrieval Agent**")
    
    # Response Generator Agent status
    if st.session_state.step_complete[2]:
        st.markdown("✅ **Response Generator Agent**")
    elif st.session_state.current_step == 2 and st.session_state.processing:
        st.markdown("🔄 **Response Generator Agent** *(Working...)*")
    else:
        st.markdown("⏳ **Response Generator Agent**")
    
    # Quality Control Agent status
    if st.session_state.step_complete[3]:
        st.markdown("✅ **Quality Control Agent**")
    elif st.session_state.current_step == 3 and st.session_state.processing:
        st.markdown("🔄 **Quality Control Agent** *(Working...)*")
    else:
        st.markdown("⏳ **Quality Control Agent**")
    
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

# Extract text from uploaded document
if uploaded_file is not None and not st.session_state.rfp_content:
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
        
    st.session_state.rfp_content = text
    
    # Show confirmation
    st.success(f"Successfully extracted {len(text)} characters from {uploaded_file.name}")

# Process RFP button - when clicked, start the process
if st.session_state.rfp_content and st.button("Start Multi-Agent Process", key="start_process"):
    st.session_state.processing = True
    st.session_state.current_step = 0
    # Use st.rerun() instead of st.experimental_rerun()
    st.rerun()

# Process flow - Document Parser Agent
if st.session_state.processing and st.session_state.current_step == 0:
    st.markdown('<div class="agent-header">🔍 Document Parser Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-status">Analyzing RFP document and extracting key requirements...</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.01)
    
    with st.spinner("Parsing document..."):
        parsed_info = parse_rfp_document(st.session_state.rfp_content)
        st.session_state.requirements = parsed_info
    
    st.session_state.step_complete[0] = True
    st.session_state.current_step = 1
    # Use st.rerun() instead of st.experimental_rerun()
    st.rerun()

# Knowledge Retrieval Agent
elif st.session_state.processing and st.session_state.current_step == 1 and st.session_state.requirements:
    st.markdown('<div class="agent-header">🧠 Knowledge Retrieval Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-status">Searching company knowledge base for relevant information...</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.01)
    
    with st.spinner("Retrieving relevant knowledge..."):
        knowledge = retrieve_relevant_knowledge(str(st.session_state.requirements))
        st.session_state.knowledge = knowledge
    
    st.session_state.step_complete[1] = True
    st.session_state.current_step = 2
    # Use st.rerun() instead of st.experimental_rerun()
    st.rerun()

# Response Generator Agent
elif st.session_state.processing and st.session_state.current_step == 2 and st.session_state.knowledge:
    st.markdown('<div class="agent-header">✍️ Response Generator Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-status">Creating draft response sections based on requirements and knowledge...</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.01)
    
    with st.spinner("Generating response draft..."):
        response_draft = generate_response_sections(str(st.session_state.requirements), st.session_state.knowledge)
        st.session_state.response_draft = response_draft
    
    st.session_state.step_complete[2] = True
    st.session_state.current_step = 3
    # Use st.rerun() instead of st.experimental_rerun()
    st.rerun()

# Quality Control Agent
elif st.session_state.processing and st.session_state.current_step == 3 and st.session_state.response_draft:
    st.markdown('<div class="agent-header">🔍 Quality Control Agent</div>', unsafe_allow_html=True)
    st.markdown('<div class="agent-status">Reviewing generated response for completeness and compliance...</div>', unsafe_allow_html=True)
    
    progress_bar = st.progress(0)
    for i in range(100):
        progress_bar.progress(i + 1)
        time.sleep(0.01)
    
    with st.spinner("Performing quality review..."):
        review = review_response(st.session_state.response_draft, str(st.session_state.requirements))
        st.session_state.review = review
    
    st.session_state.step_complete[3] = True
    st.session_state.current_step = 4
    # Use st.rerun() instead of st.experimental_rerun()
    st.rerun()

# Display results
if st.session_state.current_step == 4:
    st.markdown('<div class="success-box">', unsafe_allow_html=True)
    st.subheader("✅ RFP Processing Complete!")
    st.markdown("All agents have successfully completed their tasks.")
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
                for key, value in st.session_state.requirements.items():
                    st.markdown(f"### {key.title()}")
                    if isinstance(value, list):
                        for item in value:
                            st.markdown(f"- {item}")
                    else:
                        st.markdown(value)
        else:
            st.markdown(st.session_state.requirements)
    
    with tab2:
        st.subheader("Relevant Knowledge")
        st.markdown(st.session_state.knowledge)
    
    with tab3:
        st.subheader("Generated Response Draft")
        st.markdown(st.session_state.response_draft)
    
    with tab4:
        st.subheader("Quality Review")
        st.markdown(st.session_state.review)
    
    # Create downloadable response
    response_text = f"""# RFP Response Draft

{st.session_state.response_draft}

## Quality Review
{st.session_state.review}
"""
    
    # Create a download button with better styling
    st.markdown("### Download Complete Response")
    buffer = io.BytesIO()
    buffer.write(response_text.encode())
    buffer.seek(0)
    
    st.download_button(
        label="📥 Download Response Draft (Markdown)",
        data=buffer,
        file_name="rfp_response_draft.md",
        mime="text/markdown"
    )
    
    # Additional options
    st.markdown("### Next Steps")
    st.info("You can now review and refine the generated response before submitting.")
    
    if st.button("Start New RFP", key="reset"):
        # Reset all session state
        st.session_state.messages = []
        st.session_state.rfp_content = ""
        st.session_state.requirements = None
        st.session_state.knowledge = None
        st.session_state.response_draft = None
        st.session_state.review = None
        st.session_state.current_step = 0
        st.session_state.step_complete = [False, False, False, False]
        st.session_state.processing = False
        # Use st.rerun() instead of st.experimental_rerun()
        st.rerun()

# Display instructions if no file is uploaded
if not st.session_state.rfp_content and st.session_state.current_step == 0:
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
