import os
import json
from fastapi import FastAPI, Request, File, UploadFile, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from converter import SAPXMLParser, GeminiSQLGenerator, DataLossValidator

app = FastAPI(title="SAP XML to BigQuery SQL Converter Agent")

# Paths setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DOCS_DIR = os.path.join(BASE_DIR, "docs")
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)
os.makedirs(TEMPLATES_DIR, exist_ok=True)

# Mount static and templates
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

def read_doc_file(filename: str) -> str:
    path = os.path.join(DOCS_DIR, filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/samples")
async def list_samples():
    """
    Scans the data/ folder and returns available XML files for conversion testing.
    """
    samples = []
    if os.path.exists(DATA_DIR):
        for name in os.listdir(DATA_DIR):
            if name.endswith(".xml") and name != "placeholder.xml":
                path = os.path.join(DATA_DIR, name)
                size_kb = round(os.path.getsize(path) / 1024, 2)
                
                # Simple type check
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

@app.post("/api/convert")
async def convert_xml(
    file: UploadFile = File(None),
    sample_name: str = Form(None),
    xml_text: str = Form(None)
):
    """
    Takes an XML file (either uploaded or from preloaded samples),
    parses it, runs the Gemini SQL translator, and conducts zero-data-loss validation.
    """
    xml_content = ""
    file_name = ""

    if file:
        file_name = file.filename
        content_bytes = await file.read()
        try:
            xml_content = content_bytes.decode("utf-8")
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="Uploaded file is not a valid UTF-8 text file")
    elif sample_name:
        file_name = sample_name
        path = os.path.join(DATA_DIR, sample_name)
        if not os.path.exists(path):
            raise HTTPException(status_code=404, detail=f"Sample file {sample_name} not found")
        with open(path, "r", encoding="utf-8") as f:
            xml_content = f.read()
    elif xml_text:
        file_name = "pasted_input.xml"
        xml_content = xml_text
    else:
        raise HTTPException(status_code=400, detail="Please upload an XML file, select a sample, or paste XML content")

    if not xml_content.strip():
        raise HTTPException(status_code=400, detail="XML file content is empty")

    # 1. Parse XML Metadata
    try:
        parser = SAPXMLParser(xml_content)
        parsed_metadata = parser.parse()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse SAP XML structure: {str(e)}")

    # 2. Load BRD and reference examples
    brd_text = read_doc_file("brd_content.md")
    reference_examples_text = read_doc_file("example_sql_content.md")

    # 3. Call Gemini to Translate to SQL
    generator = GeminiSQLGenerator()
    generation_result = generator.generate_sql(parsed_metadata, brd_text, reference_examples_text)

    if not generation_result["success"]:
        return {
            "success": False,
            "filename": file_name,
            "error": generation_result.get("error", "AI translation failed"),
            "metadata": parsed_metadata,
            "sql": "",
            "validation_report": None
        }

    generated_sql = generation_result["sql"]

    # 4. Perform Data Loss Validation
    validator = DataLossValidator()
    validation_report = validator.validate(parsed_metadata, generated_sql)

    return {
        "success": True,
        "filename": file_name,
        "metadata": parsed_metadata,
        "sql": generated_sql,
        "validation_notes": generation_result["validation_notes"],
        "validation_report": validation_report
    }
