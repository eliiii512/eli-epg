from datetime import datetime, timedelta
import json
import urllib.request
import xml.etree.ElementTree as ET

# תאריכים
today = datetime.utcnow()
start_date = today.strftime("%Y/%m/%d 00:00:00")
end_date = (today + timedelta(days=5)).strftime("%Y/%m/%d 23:59:59")

url = "https://www.hot.net.il/HotCmsApiFront/api/ProgramsSchedual/GetProgramsSchedual"
payload = f'{{"ProgramsStartDateTime":"{start_date}","ProgramsEndDateTime":"{end_date}"}}'

req = urllib.request.Request(
    url,
    data=payload.encode('utf-8'),
    headers={
        "Host": "www.hot.net.il",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.hot.net.il",
        "Referer": "https://www.hot.net.il/heb/tv/tvguide/",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        source_data = response.read().decode('utf-8')
        print("--- API RESPONSE (First 500 chars) ---")
        print(source_data[:500])
        print("--- END OF RESPONSE ---")
except Exception as e:
    print(f"Error fetching data: {e}")
    source_data = ""

root = ET.Element("tv")

channels_info = [
    ("127", "ערוץ הוט Zone"),
    ("215", "ערוץ 215"),
    ("151", "ערוץ 151")
]

for ch_id, ch_name in channels_info:
    channel_elem = ET.SubElement(root, "channel", id=ch_id)
    display_name = ET.SubElement(channel_elem, "display-name", lang="he")
    display_name.text = ch_name

# בדיקת JSON
try:
    parsed = json.loads(source_data)
    print("JSON parsed successfully. Type:", type(parsed))
except Exception as err:
    print("Could not parse as JSON:", err)

# שמירה לקובץ
tree = ET.ElementTree(root)
tree.write("tv.xml", encoding="utf-8", xml_declaration=True)
print("XML generated.")
