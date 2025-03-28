import xml.etree.ElementTree as ET

def dict_to_xml(data, root_tag="data"):
    root = ET.Element(root_tag)
    _build_xml(root, data)
    return root

def _build_xml(element, data):
    if isinstance(data, dict):
        for k, v in data.items():
            sub = ET.SubElement(element, k)
            _build_xml(sub, v)
    elif isinstance(data, list):
        for item in data:
            item_el = ET.SubElement(element, "item")
            _build_xml(item_el, item)
    else:
        element.text = str(data)
