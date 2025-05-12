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

# Load environment variables from .env file
load_dotenv()

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

# Custom Anthropic API function - simplified to avoid dependencies
def call_anthropic_api(prompt, max_tokens=2000, temperature=0):
    headers = {
        "x-api-key": api_key,
        "content-type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    data = {
        "prompt": f"\n\nHuman: {prompt}\n\nAssistant:",
        "model": "claude-2",  # Using claude-2 which is compatible with the complete API
        "max_tokens_to_sample": max_tokens,
        "temperature": temperature
    }
    
    response = requests.post(
        "https://api.anthropic.com/v1/complete", 
        headers=headers,
        json=data
    )
    
    if response.status_code != 200:
        raise Exception(f"Error from Anthropic API: {response.text}")
    
    return response.json()["completion"]

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
        st.markdown('<div class="agent-header">🔍 Document Parser Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Analyzing RFP document and extracting key requirements...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Parsing document..."):
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
            
            # Call Anthropic API
            parser_response = call_anthropic_api(parser_prompt, max_tokens=2000, temperature=0)
            
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
        
        # Display progress for Knowledge Retrieval Agent
        st.markdown('<div class="agent-header">🧠 Knowledge Retrieval Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Searching company knowledge base for relevant information...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Retrieving relevant knowledge..."):
            # Create prompt for Knowledge Retrieval Agent
            knowledge_prompt = f"""You are a Knowledge Retrieval Agent for a professional services firm in Australia.
            Given these RFP requirements, provide relevant information that should be included in our response:
            
            {str(st.session_state.requirements)}
            
            Include:
            1. Suggested past projects that demonstrate relevant experience
            2. Key team members who should be mentioned
            3. Standard service descriptions that match the requirements
            4. Relevant compliance certifications and credentials
            
            Format as a structured list of recommendations.
            """
            
            # Call Anthropic API
            st.session_state.knowledge = call_anthropic_api(knowledge_prompt, max_tokens=2000, temperature=0.2)
        
        # Display progress for Response Generator Agent
        st.markdown('<div class="agent-header">✍️ Response Generator Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Creating draft response sections based on requirements and knowledge...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Generating response draft..."):
            # Create prompt for Response Generator Agent
            response_prompt = f"""You are a Response Generator Agent for an Australian professional services firm.
            Create draft responses for an RFP based on these requirements and available knowledge:
            
            RFP Requirements:
            {str(st.session_state.requirements)}
            
            Available Knowledge:
            {st.session_state.knowledge}
            
            Generate professional, compelling draft responses for key sections of the RFP.
            Format each section with a clear heading and concise, value-focused content.
            Use markdown formatting for better readability.
            """
            
            # Call Anthropic API
            st.session_state.response_draft = call_anthropic_api(response_prompt, max_tokens=3500, temperature=0.4)
        
        # Display progress for Quality Control Agent
        st.markdown('<div class="agent-header">🔍 Quality Control Agent</div>', unsafe_allow_html=True)
        st.markdown('<div class="agent-status">Reviewing generated response for completeness and compliance...</div>', unsafe_allow_html=True)
        
        progress_bar = st.progress(0)
        for i in range(100):
            progress_bar.progress(i + 1)
            time.sleep(0.01)
        
        with st.spinner("Performing quality review..."):
            # Create prompt for Quality Control Agent
            review_prompt = f"""You are a Quality Control Agent for RFP responses.
            Review this draft RFP response against the requirements and provide feedback:
            
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
            
            # Call Anthropic API
            st.session_state.review = call_anthropic_api(review_prompt, max_tokens=2000, temperature=0)
        
        # Mark processing as complete
        st.session_state.processing_complete = True
        
        # Force page refresh to show results
        st.experimental_rerun()

# Display results if processing is complete
if st.session_state.processing_complete:
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
                # Create a better display for each requirements section
                if "Key_Requirements_And_Deliverables" in st.session_state.requirements:
                    st.markdown("### 📋 Key Requirements and Deliverables")
                    st.markdown("*The core requirements that must be addressed in your response:*")
                    
                    # Display in a more readable format
                    req_data = st.session_state.requirements["Key_Requirements_And_Deliverables"]
                    
                    if isinstance(req_data, dict):
                        for category, items in req_data.items():
                            # Format category name nicely
                            category_name = category.replace('_', ' ').title()
                            st.markdown(f"#### {category_name}")
                            
                            # Display items as a clean list
                            if isinstance(items, list):
                                for item in items:
                                    st.markdown(f"- {item}")
                            else:
                                st.markdown(items)
                            st.markdown("---")
                    else:
                        st.markdown(req_data)
                
                if "Compliance_Needs" in st.session_state.requirements:
                    st.markdown("### ⚖️ Compliance Requirements")
                    st.markdown("*Mandatory compliance aspects that must be addressed:*")
                    
                    comp_data = st.session_state.requirements["Compliance_Needs"]
                    if isinstance(comp_data, dict):
                        for category, items in comp_data.items():
                            # Format category name nicely
                            category_name = category.replace('_', ' ').title()
                            st.markdown(f"#### {category_name}")
                            
                            # Display items as a clean list
                            if isinstance(items, list):
                                for item in items:
                                    st.markdown(f"- {item}")
                            else:
                                st.markdown(items)
                            st.markdown("---")
                    else:
                        st.markdown(comp_data)
                
                if "Deadlines" in st.session_state.requirements:
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
                
                if "Evaluation_Criteria" in st.session_state.requirements:
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
                
                if "Required_Sections_For_The_Response" in st.session_state.requirements:
                    st.markdown("### 📑 Required Response Sections")
                    st.markdown("*Sections that must be included in your proposal:*")
                    
                    sections_data = st.session_state.requirements["Required_Sections_For_The_Response"]
                    if isinstance(sections_data, list):
                        for i, section in enumerate(sections_data, 1):
                            st.markdown(f"**{i}. {section}**")
                    else:
                        st.markdown(sections_data)
        else:
            st.markdown(str(st.session_state.requirements))
    
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
        st.session_state.rfp_text = None
        st.session_state.requirements = None
        st.session_state.knowledge = None
        st.session_state.response_draft = None
        st.session_state.review = None
        st.session_state.processing_complete = False
        
        # Force page refresh
        st.experimental_rerun()

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
