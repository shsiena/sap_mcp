import xml.etree.ElementTree as ET

def parse_metadata(file_path):
    ns = {
        "edmx": "http://schemas.microsoft.com/ado/2007/06/edmx",
        "edm": "http://schemas.microsoft.com/ado/2008/09/edm"
    }
    tree = ET.parse(file_path)
    root = tree.getroot()

    schema = root.find(".//edm:Schema", ns)
    entity_types = {}

    for et in schema.findall("edm:EntityType", ns):
        name = et.attrib["Name"]
        properties = [
            {"name": p.attrib["Name"], "type": p.attrib["Type"]}
            for p in et.findall("edm:Property", ns)
        ]
        entity_types[name] = {"properties": properties}

    # EntitySets
    container = schema.find("edm:EntityContainer", ns)
    entity_sets = []

    for es in container.findall("edm:EntitySet", ns):
        es_name = es.attrib["Name"]
        et_full = es.attrib["EntityType"]
        et_short = et_full.split(".")[-1]

        entity_sets.append({
            "name": es_name,
            "entity_type": et_short,
            "properties": entity_types.get(et_short, {}).get("properties", [])
        })

    return entity_sets
