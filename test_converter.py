import os
import json
from converter import SAPXMLParser, DataLossValidator

def main():
    print("=== Testing SAP XML Parser ===")
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    xml_path = os.path.join(BASE_DIR, "data", "CV_SEFIR_VT_ZKSL01T.xml")
    
    if not os.path.exists(xml_path):
        print(f"Error: {xml_path} does not exist.")
        return
        
    print(f"Loading XML from {xml_path}...")
    parser = SAPXMLParser(xml_path)
    metadata = parser.parse()
    
    print("\nParsed Metadata Summary:")
    print(f"View Name: {metadata.get('name')}")
    print(f"Category: {metadata.get('dataCategory')}")
    print(f"Total Nodes: {len(metadata.get('nodes', []))}")
    print(f"Total Output Fields: {len(metadata.get('target_fields', []))}")
    
    print("\nFirst 10 Output Fields:")
    for field in metadata.get('target_fields', [])[:10]:
        print(f"  - {field['name']}: {field.get('label', '')}")
        
    print("\nView Nodes Found:")
    for node in metadata.get('nodes', []):
        print(f"  - Node '{node['name']}' (Type: {node['type']})")
        if node.get('filters'):
            print(f"    Filters: {json.dumps(node['filters'])}")
            
    print("\n=== Testing Data Loss Validator ===")
    # Simple simulated SQL containing some fields and missing others
    simulated_sql = """
    SELECT 
      RCLNT, RLDNR, RRCTY, RVERS, RYEAR, ROBJNR, COBJNR, SOBJNR, RTCUR, RUNIT,
      TSL, HSL, KSL
    FROM my_table;
    """
    
    validator = DataLossValidator()
    report = validator.validate(metadata, simulated_sql)
    
    print(f"Validation Status: {report['status']}")
    print(f"Compliance Coverage: {report['coverage']}%")
    print(f"Total XML target fields: {report['total_xml_fields']}")
    print(f"Matched target fields: {report['matched_fields']}")
    
    failed_fields = [res['xml_field'] for res in report['results'] if res['status'] == 'FAILED']
    print(f"First 10 Failed (Unmapped) Fields: {failed_fields[:10]}")
    
    print("\nBackend testing completed successfully!")

if __name__ == "__main__":
    main()
