from datetime import datetime, timedelta
import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET

# תאריכים
today = datetime.utcnow()
start_date = today.strftime("%Y/%m/%d 00:00:00")
end_date = (today + timedelta(days=5)).strftime("%Y/%m/%d 23:59:59")

url = "https://www.hot.net.il/HotCmsApiFront/api/ProgramsSchedual/GetProgramsSchedual"
payload = f'{{"ProgramsStartDateTime":"{start_date}","ProgramsEndDateTime":"{end_date}}"}'

# שימוש במחלקה שמטפלת בהפניות אוטומטית במידת הצורך
class RedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        return urllib.request.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
    def http_error_301(self, req, fp, code, msg, headers):
        return urllib.request.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)

opener = urllib.request.build_opener(RedirectHandler)
urllib.request.install_opener(opener)

req = urllib.request.Request(
    url,
    data=payload.encode('utf-8'),
    headers={
        "Host": "www.hot.net.il",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://www.hot.net.il",
        "Referer": "https://www.hot.net.il/heb/tv/tvguide/",
        "Content-Type": "application/json"
    },
    method="POST"
)

source_data = ""
try:
    with urllib.request.urlopen(req) as response:
        source_data = response.read().decode('utf-8')
        print("Data fetched successfully!")
except urllib.error.HTTPError as e:
    print(f"HTTP Error {e.code}: {e.reason}")
except urllib.error.URLError as e:
    print(f"URL Error: {e.reason}")
except Exception as e:
    print(f"Error fetching data: {e}")

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

# עיבוד הלוגיקה של התוכניות
for ch_id, ch_name in channels_info:
    target_marker = f'"channelID":"{ch_id}"'
    parts = source_data.split(target_marker)
    
    for part in parts[1:]:
        block = part.split("duration")[0] if "duration" in part else part

        title = ""
        if '"programTitle":"' in block:
            title = block.split('"programTitle":"')[1].split('"')[0].strip()

        episode = ""
        if '"programEpisode":"' in block:
            episode = block.split('"programEpisode":"')[1].split('"')[0].strip()

        raw_start = ""
        if '"programStartTime":"' in block:
            raw_start = block.split('"programStartTime":"')[1].split('"')[0].strip()

        raw_end = ""
        if '"programEndTime":"' in block:
            raw_end = block.split('"programEndTime":"')[1].split('"')[0].strip()

        try:
            dt_start = datetime.strptime(raw_start, "%Y/%m/%d %H:%M:%S") - timedelta(hours=3)
            dt_end = datetime.strptime(raw_end, "%Y/%m/%d %H:%M:%S") - timedelta(hours=3)
            start_time = dt_start.strftime("%Y%m%d%H%M%S +0000")
            end_time = dt_end.strftime("%Y%m%d%H%M%S +0000")
        except:
            start_time, end_time = "", ""

        if not title or not start_time or not end_time:
            continue

        full_title = f"{title} - פרק {episode}" if episode and episode != "0" else title

        prog_elem = ET.SubElement(root, "programme", start=start_time, stop=end_time, channel=ch_id)
        title_elem = ET.SubElement(prog_elem, "title", lang="he")
        title_elem.text = full_title

# שמירה לקובץ
tree = ET.ElementTree(root)
tree.write("tv.xml", encoding="utf-8", xml_declaration=True)
print("XMLTV generated successfully!")
