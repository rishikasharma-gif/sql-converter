import os
import re
import json
import streamlit as st
from converter import SAPXMLParser, GeminiSQLGenerator, DataLossValidator

# Set page configuration
st.set_page_config(
    page_title="SAP XML to BigQuery SQL Converter Agent",
    page_icon="⇄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Premium Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;600;700&display=swap');
    
    /* Global styles */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Inter', sans-serif;
        background-color: #f8fafc;
        color: #0f172a;
    }
    
    /* Main container padding */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Headers styling */
    h1, h2, h3, h4 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        color: #0f172a;
    }
    
    /* Top Navigation / Header */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 1.25rem 2rem;
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05), 0 1px 2px 0 rgba(0, 0, 0, 0.03);
    }
    
    .logo-container {
        display: flex;
        align-items: center;
        gap: 1rem;
    }
    
    .logo-icon {
        font-size: 2.2rem;
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
    }
    
    .logo-text h1 {
        font-size: 1.6rem;
        margin: 0;
        line-height: 1.2;
        color: #0f172a;
    }
    
    .logo-text p {
        font-size: 0.85rem;
        color: #64748b;
        margin: 0;
    }
    
    .system-status {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.2);
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        color: #047857;
        font-weight: 500;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e2e8f0;
    }
    
    /* Sidebar labels visibility and headers */
    [data-testid="stSidebar"] h3 {
        color: #0f172a !important;
    }
    
    /* Cards and Glassmorphism */
    .glass-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 16px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.025);
    }
    
    .card-title {
        font-size: 1.1rem;
        margin-top: 0;
        margin-bottom: 1rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        border-bottom: 1px solid #f1f5f9;
        padding-bottom: 0.5rem;
        color: #0f172a;
    }
    
    /* Meter / Audit dial */
    .audit-container {
        text-align: center;
        padding: 1rem 0;
    }
    
    .audit-score {
        font-size: 3rem;
        font-weight: 800;
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    
    .audit-label {
        font-size: 0.9rem;
        color: #64748b;
        font-weight: 500;
    }
    
    /* Active file indicator */
    .active-file-box {
        background: #f1f5f9;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        margin-bottom: 1.5rem;
        font-size: 0.9rem;
        color: #475569;
    }
    .active-file-box span {
        color: #2563eb;
        font-weight: 600;
    }
    
    /* Custom Table styling */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 0.5rem;
    }
    .custom-table th {
        text-align: left;
        padding: 0.75rem 1rem;
        background-color: #f8fafc;
        color: #475569;
        font-weight: 600;
        font-size: 0.85rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .custom-table td {
        padding: 0.75rem 1rem;
        border-bottom: 1px solid #f1f5f9;
        font-size: 0.85rem;
        vertical-align: middle;
        color: #0f172a;
    }
    
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.5rem;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.75rem;
    }
    .status-passed {
        background-color: rgba(16, 185, 129, 0.1);
        color: #047857;
        border: 1px solid rgba(16, 185, 129, 0.2);
    }
    .status-failed {
        background-color: rgba(239, 68, 68, 0.1);
        color: #b91c1c;
        border: 1px solid rgba(239, 68, 68, 0.2);
    }
    
    /* Code container style */
    .code-container {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# Project paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

def read_doc_file(filename: str) -> str:
    path = os.path.join(DOCS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def list_samples():
    samples = []
    if os.path.exists(DATA_DIR):
        for name in os.listdir(DATA_DIR):
            if name.endswith(".xml") and name != "placeholder.xml":
                path = os.path.join(DATA_DIR, name)
                size_kb = round(os.path.getsize(path) / 1024, 2)
                xml_type = "Calculation View"
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        head = f.read(500)
                        if "CompositeProvider" in head or "composite" in head.lower():
                            xml_type = "Composite Provider"
                except:
                    pass
                samples.append({
                    "name": name,
                    "size_kb": size_kb,
                    "type": xml_type
                })
    return samples

# Header
st.markdown("""
<div class="header-container">
    <div class="logo-container">
        <div class="logo-icon">⇄</div>
        <div class="logo-text">
            <h1>SQL Converter Agent</h1>
            <p>SAP HANA XML models to optimized BigQuery standard SQL</p>
        </div>
    </div>
    <div class="system-status">
        <div class="status-dot"></div>
        <span>Agent Online</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Sidebar
st.sidebar.markdown('<h3 class="card-title">📁 File Selector</h3>', unsafe_allow_html=True)

# File Uploader
uploaded_file = st.sidebar.file_uploader("Upload SAP XML Model", type=["xml"], label_visibility="collapsed")

# Scan samples
samples = list_samples()
sample_options = ["None"] + [s["name"] for s in samples]

st.sidebar.markdown("<div style='margin: 1rem 0; text-align: center; color: #64748b; font-size: 0.8rem; font-weight: bold;'>OR CHOOSE PRELOADED SAMPLE</div>", unsafe_allow_html=True)
selected_sample = st.sidebar.selectbox("Preloaded Sample", options=sample_options, label_visibility="collapsed")

# Process source Selection
xml_content = ""
file_name = ""

if uploaded_file is not None:
    file_name = uploaded_file.name
    xml_content = uploaded_file.getvalue().decode("utf-8")
elif selected_sample != "None":
    file_name = selected_sample
    sample_path = os.path.join(DATA_DIR, selected_sample)
    if os.path.exists(sample_path):
        with open(sample_path, "r", encoding="utf-8") as f:
            xml_content = f.read()

# Sidebar: Audit panel details (updated reactively)
audit_placeholder = st.sidebar.empty()

# Main Area
if xml_content:
    st.markdown(f"""
    <div class="active-file-box">
        Active File: <span>{file_name}</span>
    </div>
    """, unsafe_allow_html=True)
    
    # Process conversion with spinner
    with st.spinner("Processing SAP XML View & Generating SQL..."):
        try:
            # 1. Parse XML Metadata
            parser = SAPXMLParser(xml_content)
            parsed_metadata = parser.parse()
            
            # 2. Load BRD and reference examples
            brd_text = read_doc_file("brd_content.md")
            reference_examples_text = read_doc_file("example_sql_content.md")
            
            # 3. Call Gemini to Translate to SQL
            generator = GeminiSQLGenerator()
            generation_result = generator.generate_sql(parsed_metadata, brd_text, reference_examples_text)
            
            if generation_result.get("success"):
                generated_sql = generation_result.get("optimized_sql", "")
                normal_sql = generation_result.get("normal_sql", "")
                metadata_table = generation_result.get("metadata_table", "")
                
                # 4. Perform Data Loss Validation
                validator = DataLossValidator()
                validation_report = validator.validate(parsed_metadata, generated_sql)
                coverage = validation_report.get("coverage", 0.0)
                status_text = validation_report.get("status", "PENDING")
                
                # Update Audit panel in the sidebar
                status_color = "#10b981" if status_text == "PASSED" else "#ef4444"
                audit_placeholder.markdown(f"""
                <div class="glass-card">
                    <h3 class="card-title">🛡️ Data-Loss Audit</h3>
                    <div class="audit-container">
                        <div class="audit-label">FIELD COVERAGE</div>
                        <div class="audit-score">{coverage}%</div>
                        <div class="status-badge" style="background-color: {status_color}15; color: {status_color}; border: 1px solid {status_color}30;">
                            {status_text}
                        </div>
                        <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.8rem;">
                            {validation_report.get('matched_fields', 0)} of {validation_report.get('total_xml_fields', 0)} fields mapped
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Render code workspace tabs
                tab_sql, tab_normal_sql, tab_graph = st.tabs(["Optimized BigQuery SQL", "Normal SQL", "Parsed Logical Graph"])
                
                with tab_sql:
                    # Action buttons: Download & Copy (Download is built-in, copy can use code block)
                    st.download_button(
                        label="⇩ Download Optimized SQL File",
                        data=generated_sql,
                        file_name=f"{os.path.splitext(file_name)[0]}_optimized.sql",
                        mime="text/x-sql"
                    )
                    st.code(generated_sql, language="sql")
                    
                with tab_normal_sql:
                    st.download_button(
                        label="⇩ Download Normal SQL File",
                        data=normal_sql,
                        file_name=f"{os.path.splitext(file_name)[0]}_normal.sql",
                        mime="text/x-sql"
                    )
                    st.code(normal_sql, language="sql")
                    
                with tab_graph:
                    st.json(parsed_metadata)
                    
                # Bottom validation checklist & notes
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("""
                    <div class="glass-card" style="height: 100%;">
                        <h3 class="card-title">🔍 Field Compliance Checklist</h3>
                    """, unsafe_allow_html=True)
                    
                    # Construct compliance checklist HTML table
                    table_rows = ""
                    for res in validation_report.get("results", []):
                        badge_class = "status-passed" if res["status"] == "PASSED" else "status-failed"
                        table_rows += f"""
                        <tr>
                            <td><code>{res['xml_field']}</code></td>
                            <td>{res['label']}</td>
                            <td><span class="status-badge {badge_class}">{res['status']}</span></td>
                            <td style="color: #334155;">{res['notes']}</td>
                        </tr>
                        """
                    
                    st.markdown(f"""
                        <div style="max-height: 400px; overflow-y: auto;">
                            <table class="custom-table">
                                <thead>
                                    <tr>
                                        <th>SAP XML Element</th>
                                        <th>Friendly Label</th>
                                        <th>Status</th>
                                        <th>Notes</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {table_rows}
                                </tbody>
                            </table>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with col2:
                    st.markdown("""
                    <div class="glass-card" style="height: 100%;">
                        <h3 class="card-title">💡 Metadata Table</h3>
                        <div style="max-height: 400px; overflow-y: auto; color: #334155; font-size: 0.9rem;">
                    """, unsafe_allow_html=True)
                    
                    if metadata_table:
                        st.markdown(metadata_table)
                    else:
                        st.markdown("<p style='color: #64748b;'>No metadata table generated.</p>", unsafe_allow_html=True)
                        
                    st.markdown("""
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
            else:
                st.error(f"Failed to generate SQL: {generation_result.get('error')}")
                audit_placeholder.markdown("""
                <div class="glass-card">
                    <h3 class="card-title">🛡️ Data-Loss Audit</h3>
                    <div class="audit-container">
                        <div class="status-badge status-failed">ERROR</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"An unexpected error occurred during parsing or generation: {str(e)}")
            
else:
    # Sidebar default audit state
    audit_placeholder.markdown("""
    <div class="glass-card">
        <h3 class="card-title">🛡️ Data-Loss Audit</h3>
        <div class="audit-container">
            <div class="audit-label">FIELD COVERAGE</div>
            <div class="audit-score">0%</div>
            <div class="status-badge" style="background-color: rgba(100, 116, 139, 0.1); color: #475569; border: 1px solid rgba(100, 116, 139, 0.2);">
                PENDING
            </div>
            <div style="font-size: 0.8rem; color: #64748b; margin-top: 0.8rem;">
                Select a file to run audit
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Dashboard placeholder view
    st.markdown("""
    <div class="glass-card" style="text-align: center; padding: 5rem 2rem; margin-top: 2rem;">
        <div style="font-size: 4rem; margin-bottom: 1.5rem; background: linear-gradient(135deg, #4f46e5 0%, #06b6d4 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">⇄</div>
        <h2>Welcome to the SQL Converter Agent</h2>
        <p style="color: #475569; max-width: 600px; margin: 0.5rem auto 2rem auto; font-size: 1.05rem;">
            Upload a SAP XML calculation model or select a preloaded sample in the sidebar to generate optimized BigQuery SQL with automated data-loss audits.
        </p>
    </div>
    """, unsafe_allow_html=True)
