import streamlit as st
import anthropic
import json
from io import StringIO
import pypdf
import docx

# --- Helper Functions for File Reading ---
def read_file_content(uploaded_file):
    """
    Reads text from uploaded .txt, .pdf, or .docx files.
    Returns the extracted text as a string.
    """
    if uploaded_file is None:
        return ""
    
    try:
        # Handle PDF files
        if uploaded_file.type == "application/pdf":
            reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
            return text
        
        # Handle Word documents
        elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(uploaded_file)
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        
        # Handle Plain Text files
        else: 
            # Decode bytes to string
            stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
            return stringio.read()
            
    except Exception as e:
        st.error(f"Error reading file: {e}")
        return ""

# --- Page Configuration ---
st.set_page_config(
    page_title="Orane Contract Analyzer",
    page_icon="⚖️",
    layout="wide"
)

# --- CSS Styling ---
# This mimics the look and feel of the React cards using CSS grid/flexbox
st.markdown("""
<style>
    .metric-card {
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e5e7eb;
        text-align: center;
        background-color: white;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .metric-card h3 {
        margin: 0;
        font-size: 1.875rem;
        line-height: 2.25rem;
        font-weight: 700;
    }
    .metric-card p {
        margin: 0;
        font-size: 0.875rem;
        line-height: 1.25rem;
        font-weight: 500;
    }
    
    /* Severity Colors */
    .critical { background-color: #fef2f2; border-color: #fecaca; }
    .critical h3 { color: #dc2626; }
    .critical p { color: #b91c1c; }
    
    .moderate { background-color: #fff7ed; border-color: #fed7aa; }
    .moderate h3 { color: #ea580c; }
    .moderate p { color: #c2410c; }
    
    .minor { background-color: #fefce8; border-color: #fef08a; }
    .minor h3 { color: #ca8a04; }
    .minor p { color: #a16207; }
    
    /* Risk Badges */
    .risk-high { background-color: #fee2e2; color: #dc2626; border-color: #fecaca; }
    .risk-medium { background-color: #ffedd5; color: #ea580c; border-color: #fed7aa; }
    .risk-low { background-color: #dcfce7; color: #16a34a; border-color: #bbf7d0; }
    
    /* Header styling */
    h1 { color: #1f2937; }
</style>
""", unsafe_allow_html=True)

# --- Sidebar (API Key Input) ---
with st.sidebar:
    st.header("⚙️ Configuration")
    api_key = st.text_input(
        "Anthropic API Key", 
        type="password", 
        help="Enter your Claude API Key here. It starts with 'sk-ant...'"
    )
    st.info("Your API key is not stored. It is used only for this session.")
    st.markdown("[Get an API key here](https://console.anthropic.com/)")

# --- Main App Interface ---

# Title Section
col1, col2 = st.columns([1, 15])
with col1:
    st.write("# ⚖️") 
with col2:
    st.title("Orane Contract Compliance Analyzer")

st.markdown("""
This tool compares a **Third-Party Contract** against **Orane's Standard Contract** to automatically identify 
violations, critical deviations, and business risks.
""")

st.divider()

# --- File Upload Section ---
col_orane, col_third = st.columns(2)

# Column 1: Standard Contract
with col_orane:
    st.subheader("1. Orane's Standard Contract")
    orane_file = st.file_uploader("Upload Standard Contract", type=['txt', 'pdf', 'docx'], key="orane")
    
    # Initialize session state for text if it doesn't exist
    if "orane_text" not in st.session_state:
        st.session_state.orane_text = ""

    # If file is uploaded, extract text
    if orane_file:
        content = read_file_content(orane_file)
        if content != st.session_state.orane_text:
            st.session_state.orane_text = content
            
    # Text Area for manual editing or viewing
    orane_text = st.text_area(
        "Standard Contract Text", 
        value=st.session_state.orane_text, 
        height=300,
        placeholder="Paste text here or upload a file above..."
    )
    if orane_text:
        st.success(f"Loaded {len(orane_text)} characters")

# Column 2: Third Party Contract
with col_third:
    st.subheader("2. Third-Party Contract")
    third_file = st.file_uploader("Upload Third-Party Contract", type=['txt', 'pdf', 'docx'], key="third")
    
    if "third_text" not in st.session_state:
        st.session_state.third_text = ""

    if third_file:
        content = read_file_content(third_file)
        if content != st.session_state.third_text:
            st.session_state.third_text = content
            
    third_text = st.text_area(
        "Third-Party Contract Text", 
        value=st.session_state.third_text, 
        height=300,
        placeholder="Paste text here or upload a file above..."
    )
    if third_text:
        st.success(f"Loaded {len(third_text)} characters")

# --- Analyze Button ---
st.divider()
analyze_btn = st.button("🔍 Analyze Contracts for Violations", type="primary", use_container_width=True)

# --- Logic: Call AI ---
if analyze_btn:
    # Validation
    if not api_key:
        st.error("❌ Please enter your Anthropic API Key in the sidebar to proceed.")
    elif not orane_text or not third_text:
        st.warning("⚠️ Please ensure both contracts have text loaded before analyzing.")
    else:
        # Initialize Client
        client = anthropic.Anthropic(api_key=api_key)
        
        # Construct Prompt
        prompt = f"""You are a legal contract analysis AI. Compare the third-party contract against Orane's standard contract and identify violations, deviations, and risks.

ORANE'S STANDARD CONTRACT:
{orane_text}

THIRD-PARTY CONTRACT TO ANALYZE:
{third_text}

Analyze the third-party contract and provide a JSON response with the following structure (respond ONLY with valid JSON, no markdown):
{{
  "summary": {{
    "totalIssues": number,
    "criticalViolations": number,
    "moderateDeviations": number,
    "minorConcerns": number,
    "overallRisk": "HIGH" | "MEDIUM" | "LOW"
  }},
  "violations": [
    {{
      "category": "Payment Terms" | "Liability" | "Termination" | "IP Rights" | "Confidentiality" | "Warranties" | "Jurisdiction" | "Other",
      "severity": "CRITICAL" | "MODERATE" | "MINOR",
      "title": "Brief title of the issue",
      "oraneClause": "Relevant clause from Orane's contract",
      "thirdPartyClause": "Relevant clause from third-party contract",
      "violation": "Detailed explanation of how it violates or deviates",
      "recommendation": "Suggested action or amendment",
      "riskImpact": "Business/legal risk this poses"
    }}
  ]
}}"""

        try:
            with st.spinner("🤖 Analyzing contracts... This may take up to 30 seconds."):
                # Call Claude API
                message = client.messages.create(
                    model="claude-3-5-sonnet-20240620",
                    max_tokens=4000,
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract Response
                response_text = message.content[0].text
                
                # Clean JSON (remove markdown code blocks if present)
                clean_json = response_text.replace("```json", "").replace("```", "").strip()
                
                # Parse JSON
                analysis = json.loads(clean_json)
                
                # Save to session state so it doesn't disappear on refresh
                st.session_state.analysis_result = analysis

        except anthropic.APIError as e:
            st.error(f"Anthropic API Error: {str(e)}")
        except json.JSONDecodeError:
            st.error("Error parsing AI response. The model did not return valid JSON. Please try again.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {str(e)}")

# --- Display Results ---
if "analysis_result" in st.session_state:
    data = st.session_state.analysis_result
    summary = data.get("summary", {})
    
    st.markdown("## 📊 Analysis Report")
    
    # 1. Summary Metrics Display
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="metric-card critical">
            <h3>{summary.get("criticalViolations", 0)}</h3>
            <p>Critical Violations</p>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card moderate">
            <h3>{summary.get("moderateDeviations", 0)}</h3>
            <p>Moderate Deviations</p>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="metric-card minor">
            <h3>{summary.get("minorConcerns", 0)}</h3>
            <p>Minor Concerns</p>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        risk = summary.get("overallRisk", "UNKNOWN")
        risk_class = f"risk-{risk.lower()}" if risk.lower() in ["high", "medium", "low"] else ""
        st.markdown(f"""
        <div class="metric-card {risk_class}">
            <h3>{risk}</h3>
            <p>Overall Risk</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("") # Spacer

    # 2. Detailed Violations List
    st.subheader("Detailed Findings")
    violations = data.get("violations", [])
    
    if not violations:
        st.info("No violations found! The contracts seem to align perfectly.")
    
    for i, v in enumerate(violations):
        # Set icon based on severity
        severity = v.get('severity', 'MINOR')
        if severity == "CRITICAL":
            icon = "🔴"
        elif severity == "MODERATE":
            icon = "🟠"
        else:
            icon = "🟡"
            
        with st.expander(f"{icon} {v.get('title', 'Issue')} ({v.get('category', 'General')})"):
            st.caption(f"**Severity:** {severity}")
            
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**📋 Orane's Standard:**\n\n_{v.get('oraneClause', 'N/A')}_")
            with c2:
                st.error(f"**⚠️ Third-Party Clause:**\n\n_{v.get('thirdPartyClause', 'N/A')}_")
            
            st.markdown(f"**🔍 Violation Details:** \n{v.get('violation', 'No details provided.')}")
            st.markdown(f"**💼 Risk Impact:** \n{v.get('riskImpact', 'No risk impact provided.')}")
            st.success(f"**💡 Recommendation:** \n{v.get('recommendation', 'No recommendation provided.')}")

# --- Footer ---
st.divider()
st.caption("Contract Compliance Analyzer • Built with Streamlit & Claude")
