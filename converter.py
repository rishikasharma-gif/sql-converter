import os
import re
import json
import xml.etree.ElementTree as ET
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv(override=True)

class SAPXMLParser:
    """
    Parses SAP HANA Calculation View / Composite Provider XML schemas
    into a simplified, human-readable JSON representation.
    """
    def __init__(self, xml_content_or_path: str):
        self.xml_content_or_path = xml_content_or_path.strip()
        if self.xml_content_or_path.startswith("<?xml") or self.xml_content_or_path.startswith("<"):
            self.root = ET.fromstring(self.xml_content_or_path)
        else:
            self.tree = ET.parse(self.xml_content_or_path)
            self.root = self.tree.getroot()

    def parse(self) -> dict:
        metadata = {
            "name": self.root.get("name") or "Unnamed_View",
            "dataCategory": self.root.get("dataCategory") or "CUBE",
            "defaultNode": self.root.get("defaultNode") or "",
            "nodes": [],
            "target_fields": []
        }

        # Parse target output fields from the root or the final logical node
        # Many SAP calculation views define logical target columns at the top level
        for logical_col in self.root.findall(".//logicalModel/attributes/attribute"):
            metadata["target_fields"].append({
                "name": logical_col.get("name"),
                "label": logical_col.find("endUserTexts").get("label") if logical_col.find("endUserTexts") is not None else logical_col.get("name")
            })
        for measure in self.root.findall(".//logicalModel/measures/measure"):
            metadata["target_fields"].append({
                "name": measure.get("name"),
                "label": measure.find("endUserTexts").get("label") if measure.find("endUserTexts") is not None else measure.get("name")
            })

        # Process each viewNode (logical query blocks like Projection, Join, Union, Aggregation)
        for view_node in self.root.findall(".//viewNode"):
            node_name = view_node.get("name")
            node_type = (
                view_node.get("{http://www.w3.org/2001/XMLSchema-instance}type") 
                or view_node.get("xsi:type") 
                or "Unknown"
            )

            # Strip XML namespace prefixes for cleaner representation
            if ":" in node_type:
                node_type = node_type.split(":")[-1]

            node_info = {
                "name": node_name,
                "type": node_type,
                "elements": [],
                "inputs": [],
                "filters": []
            }

            # Parse elements (columns, formulas, calculations) defined in this node
            for elem in view_node.findall("element"):
                elem_name = elem.get("name")
                agg_behavior = elem.get("aggregationBehavior")
                
                elem_info = {
                    "name": elem_name,
                    "aggregationBehavior": agg_behavior
                }

                # Extract calculated column formulas
                calc = elem.find("calculationDefinition")
                if calc is not None:
                    formula = calc.find("formula")
                    if formula is not None:
                        elem_info["formula"] = formula.text

                node_info["elements"].append(elem_info)

            # Parse inputs and element mappings
            for inp in view_node.findall("input"):
                inp_info = {
                    "source": None,
                    "mappings": []
                }

                entity = inp.find("entity")
                if entity is not None:
                    inp_info["source"] = entity.text
                else:
                    vnode = inp.find("viewNode")
                    if vnode is not None:
                        inp_info["source"] = vnode.text

                for mapping in inp.findall("mapping"):
                    target = mapping.get("targetName")
                    source = mapping.get("sourceName")
                    inp_info["mappings"].append({"target": target, "source": source})

                node_info["inputs"].append(inp_info)

            # Parse element filters (equivalent to WHERE clauses)
            for flt in view_node.findall("elementFilter"):
                flt_elem = flt.get("elementName")
                val_flt = flt.find("valueFilter")
                if val_flt is not None:
                    flt_type = (
                        val_flt.get("{http://www.w3.org/2001/XMLSchema-instance}type") 
                        or val_flt.get("xsi:type") 
                        or ""
                    )
                    if ":" in flt_type:
                        flt_type = flt_type.split(":")[-1]
                    
                    flt_operator = val_flt.get("operator") or "="
                    flt_value = val_flt.get("value")
                    operands = [op.get("value") for op in val_flt.findall("operands")]

                    filter_info = {
                        "column": flt_elem,
                        "type": flt_type,
                        "operator": flt_operator,
                        "value": flt_value,
                        "operands": operands
                    }
                    node_info["filters"].append(filter_info)

            node_info = {k: v for k, v in node_info.items() if v or k in ("name", "type")}
            metadata["nodes"].append(node_info)

        # Fallback for target fields if logicalModel didn't yield columns
        if not metadata["target_fields"] and metadata["nodes"]:
            # Pick the default / final node elements as target fields
            def_node = metadata["defaultNode"].replace("#//", "")
            for node in metadata["nodes"]:
                if node.get("name") == def_node or node.get("type") == "Aggregation":
                    metadata["target_fields"] = [{"name": e["name"], "label": e["name"]} for e in node.get("elements", [])]
                    break

        return metadata


class GeminiSQLGenerator:
    """
    Integrates with the Gemini API to translate parsed XML models into optimized BigQuery SQL,
    referencing migration best practices and user-provided conversions.
    """
    def __init__(self):
        # Retrieve the API key from environment variables
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError("GEMINI_API_KEY not set in environment. Please add it to .env or export it.")
        # Detect obvious placeholder values and reject them
        placeholder_indicators = ["YOUR_ACTUAL_KEY", "PLACEHOLDER", "YOUR_", "REPLACE_ME"]
        if any(indicator in api_key for indicator in placeholder_indicators):
            raise RuntimeError("GEMINI_API_KEY appears to be a placeholder value. Replace it with a valid Gemini API key.")
        self.client = genai.Client(api_key=api_key)

    def generate_sql(self, parsed_metadata: dict, brd_text: str, reference_examples_text: str) -> dict:
        # Construct the system instruction prompt
        system_instruction = (
            "You are an expert Google BigQuery Data Architect specializing in SAP HANA Calculation View migrations.\n"
            "Your task is to convert SAP Calculation View metadata (JSON format) into optimized BigQuery SQL.\n"
            "Strictly enforce zero data loss. Map every source field and calculation correctly into BigQuery standard SQL.\n"
            "Use optimized techniques like WITH (CTEs) representing projection/join/union nodes, CROSS JOIN UNNEST for unpivoting,\n"
            "and appropriate analytical/aggregate functions. Align your SQL style with the provided reference conversion patterns.\n"
            "Ensure that you output your response in JSON format containing two keys:\n"
            "1) 'sql': The complete, optimized, ready-to-run BigQuery SQL query.\n"
            "2) 'validation_notes': An array of strings explaining how complex structures or custom formulas were mapped, "
            "and flagging any manual checks required."
        )

        prompt = f"""
### 1. BUSINESS REQUIREMENTS & STANDARDS
{brd_text}

### 2. REFERENCE CONVERSION EXAMPLES (HANA XML -> BigQuery SQL)
{reference_examples_text}

### 3. SOURCE METADATA TO CONVERT (PARSED FROM SAP XML)
{json.dumps(parsed_metadata, indent=2)}

### INSTRUCTIONS:
- Analyze the parsed metadata (nodes, mappings, formulas, filters, and output target_fields).
- Synthesize an optimized BigQuery SQL query matching the input dataflow graph.
- Align with the naming conventions and structure patterns of the reference examples.
- Return a JSON object with the keys 'sql' and 'validation_notes' as defined.
"""

        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    safety_settings=[
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                        types.SafetySetting(
                            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                            threshold=types.HarmBlockThreshold.BLOCK_NONE,
                        ),
                    ]
                )
            )
            
            clean_text = response.text.strip()
            # Clean markdown code blocks if any exist
            if clean_text.startswith("```json"):
                clean_text = clean_text[7:]
            if clean_text.startswith("```"):
                clean_text = clean_text[3:]
            if clean_text.endswith("```"):
                clean_text = clean_text[:-3]
            clean_text = clean_text.strip()

            # Escape raw backslashes that aren't part of a valid JSON escape sequence.
            # JSON allows: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX
            clean_text = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', clean_text)

            result = json.loads(clean_text)
            return {
                "success": True,
                "sql": result.get("sql", ""),
                "validation_notes": result.get("validation_notes", [])
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to generate SQL via Gemini API: {str(e)}",
                "sql": "",
                "validation_notes": []
            }


class DataLossValidator:
    """
    Performs field-level compliance verification between target XML columns 
    and SELECT elements in the generated BigQuery SQL query.
    """
    @staticmethod
    def validate(parsed_metadata: dict, sql_text: str) -> dict:
        target_fields = parsed_metadata.get("target_fields", [])
        if not target_fields:
            return {"status": "SKIPPED", "message": "No target fields found in XML metadata", "coverage": 0, "results": []}

        # Normalize SQL for easier parsing (remove comments, line breaks)
        sql_clean = re.sub(r'--.*$', '', sql_text, flags=re.MULTILINE)
        sql_clean = re.sub(r'/\*.*?\*/', '', sql_clean, flags=re.DOTALL)
        sql_clean = sql_clean.upper()

        results = []
        matched_count = 0

        for field in target_fields:
            field_name = field["name"].upper()
            # Simple regex search for field occurrences in SELECT blocks or alias blocks (e.g. 'AS FIELD_NAME', 'FIELD_NAME,')
            # Look for word boundaries
            pattern = re.compile(rf'\b{field_name}\b')
            matched = bool(pattern.search(sql_clean))
            
            if matched:
                matched_count += 1
                status = "PASSED"
                notes = "Field is mapped in the generated SQL statement"
            else:
                status = "FAILED"
                notes = "Field is missing from the generated SQL statement (potential data loss!)"

            results.append({
                "xml_field": field["name"],
                "label": field.get("label", ""),
                "status": status,
                "notes": notes
            })

        coverage = round((matched_count / len(target_fields)) * 100, 2) if target_fields else 0
        overall_status = "PASSED" if coverage == 100 else "WARNING"

        return {
            "status": overall_status,
            "coverage": coverage,
            "total_xml_fields": len(target_fields),
            "matched_fields": matched_count,
            "results": results
        }
