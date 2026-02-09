# Get in text format: https://content.openalex.org/works/W2741809807.grobid-xml 

# Check if XML is available:
# https://api.openalex.org/works?filter=default.search:artificial%20intelligence,has_content.grobid_xml:true&api_key=YOUR_KEY

"""
Check if it has PDF or XML:
r = requests.get(url).json()
print(r["has_content"])
"""

import os
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("API_KEY")


url = f"https://content.openalex.org/works/W2626778328.pdf?api_key={API_KEY}"
r = requests.get(url)

with open("paper.pdf", "wb") as f:
    f.write(r.content)

print("PDF downloaded as paper.pdf")

# --> Result: Downloads an empty PDF