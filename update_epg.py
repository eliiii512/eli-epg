import json
from datetime import datetime, timedelta
import urllib.request
import xml.etree.ElementTree as ET

# הגדרת תאריכים (מהיום למשך 5 קדימה)
today = datetime.utcnow()
start_date = today.strftime("%Y/%m/%d 00:00:00")
end_date = (today + timedelta(days=5)).strftime("%Y/%m/%d 23:59:59")

url = "https://www.hot.net.il/HotCmsApiFront/api/ProgramsSchedual/GetProgramsSchedual"
payload = {
    "ProgramsStartDateTime": start_date,
    "ProgramsEndDateTime": end_date
}

req = urllib.request.Request(
    url,
    data=json.dumps(payload).encode('utf-8'),
    headers={
        "Host": "www.hot.net.il",
        "Origin": "https://www.hot.net.il",
        "Referer": "https://www.hot.net.il/heb/tv/tvguide/",
        "Content-Type": "application/json",
        "Accept": "application/json, text/plain, */*",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        res_data = json.loads(response.read().decode('utf-8'))
        programs_list = res_data.get("data", {}).get("programsDetails", [])
        if not programs_list and isinstance(res_data, list):
            programs_list = res_data
except Exception as e:
    print(f"Error fetching data: {e}")
    programs_list = []

# יצירת מבנה XMLTV
root = ET.Element("tv")

# הגדרת הערוצים
channels_info = [
    ("127", "ערוץ הוט Zone"),
    ("215", "ערוץ 215"),
    ("151", "ערוץ 151")
]

for ch_id, ch_name in channels_info:
    channel_elem = ET.SubElement(root, "channel", id=ch_id)
    display_name = ET.SubElement(channel_elem, "display-name", lang="he")
    display_name.text = ch_name

# המרת זמן משעון ישראל ל־UTC עבור XMLTV
def convert_time(time_str):
    try:
        dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
        dt_utc = dt - timedelta(hours=3) # קיזוז שעון קיץ ישראל
        return dt_utc.strftime("%Y%m%d%H%M%S +0000")
    except:
        return ""

for item in programs_list:
    ch_id = str(item.get("channelID", ""))
    if ch_id in ["127", "215", "151"]:
        title = item.get("programTitle", "").strip()
        synopsis = item.get("synopsis", "").strip()
        raw_start = item.get("programStartTime", "")
        raw_end = item.get("programEndTime", "")
        
        start_time = convert_time(raw_start)
        end_time = convert_time(raw_end)
        
        if not title or not start_time or not end_time:
            continue

        # עיבוד שמות ותוספת פרקים בהתאם לערוץ
        if ch_id in ["127", "215"]:
            episode = item.get("programEpisode", "").strip()
            if episode and episode != "0":
                full_title = f"{title} - פרק {episode}"
            else:
                full_title = title
        else:
            full_title = title

        prog_elem = ET.SubElement(root, "programme", start=start_time, stop=end_time, channel=ch_id)
        
        title_elem = ET.SubElement(prog_elem, "title", lang="he")
        title_elem.text = full_title
        
        if synopsis:
            desc_elem = ET.SubElement(prog_elem, "desc", lang="he")
            desc_elem.text = synopsis

# שמירה לקובץ
tree = ET.ElementTree(root)
tree.write("tv.xml", encoding="utf-8", xml_declaration=True)
print("XMLTV file generated successfully!")
