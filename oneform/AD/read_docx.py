import zipfile
import xml.etree.ElementTree as ET

def extract_text_from_docx(path):
    try:
        with zipfile.ZipFile(path) as docx:
            xml_content = docx.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            
            # Namespaces
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            
            texts = []
            for paragraph in tree.findall('.//w:p', ns):
                para_text = ""
                for run in paragraph.findall('.//w:r', ns):
                    for text in run.findall('.//w:t', ns):
                        if text.text:
                            para_text += text.text
                if para_text:
                    texts.append(para_text)
            return "\n".join(texts)
    except Exception as e:
        return str(e)

if __name__ == "__main__":
    print(extract_text_from_docx('D:/oneform/AD/Search Ads.docx'))
