from datetime import datetime, timedelta
import urllib.request
import xml.etree.ElementTree as ET

# תאריכים דינמיים לפי OpenBullet
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
        "Accept-Language": "he-IL,he;q=0.9,en-US;q=0.8,en-O;q=0.7",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as response:
        source_data = response.read().decode('utf-8')
except Exception as e:
    print(f"Error fetching data: {e}")
    source_data = ""

root = ET.Element("tv")

# הגדרת ערוצים
channels_info = [
    ("127", "ערוץ הוט Zone"),
    ("215", "ערוץ 215"),
    ("151", "ערוץ 151")
]

for ch_id, ch_name in channels_info:
    channel_elem = ET.SubElement(root, "channel", id=ch_id)
    display_name = ET.SubElement(channel_elem, "display-name", lang="he")
    display_name.text = ch_name

def convert_time(time_str):
    try:
        dt = datetime.strptime(time_str, "%Y/%m/%d %H:%M:%S")
        dt_utc = dt - timedelta(hours=3)
        return dt_utc.strftime("%Y%m%d%H%M%S +0000")
    except:
        return ""

# לוגיקה בדיוק כמו ב-OpenBullet לכל ערוץ
for ch_id, ch_name in channels_info:
    target_marker = f'"channelID":"{ch_id}"'
    parts = source_data.split(target_marker)
    
    # החלק הראשון הוא לפני המופע הראשון, לכן מתחילים מ-1
    for part in parts[1:]:
        # חיתוך עד ה-"duration" בדיוק כמו ב-OpenBullet
        if "duration" in part:
            block = part.split("duration")[0]
        else:
            block = part

        # שליפת שם תוכנית (Title)
        title = ""
        if '"programTitle":"' in block:
            title_part = block.split('"programTitle":"')[1]
            title = title_part.split('"')[0].strip()

        # שליפת מספר פרק (Episode)
        episode = ""
        if '"programEpisode":"' in block:
            ep_part = block.split('"programEpisode":"')[1]
            episode = ep_part.split('"')[0].strip()

        # שליפת שעת התחלה
        raw_start = ""
        if '"programStartTime":"' in block:
            start_part = block.split('"programStartTime":"')[1]
            raw_start = start_part.split('"')[0].strip()

        # שליפת שעת סיום
        raw_end = ""
        if '"programEndTime":"' in block:
            end_part = block.split('"programEndTime":"')[1]
            raw_end = end_part.split('"')[0].strip()

        start_time = convert_time(raw_start)
        end_time = convert_time(raw_end)

        if not title or not start_time or not end_time:
            continue

        # הוספת מספר פרק לשם התוכנית במידה וקיים (בעיקר לערוצי סדרות כמו 127 ו־215)
        if episode and episode != "0":
            full_title = f"{title} - פרק {episode}"
        else:
            full_title = title

        prog_elem = ET.SubElement(root, "programme", start=start_time, stop=end_time, channel=ch_id)
        
        title_elem = ET.SubElement(prog_elem, "title", lang="he")
        title_elem.text = full_title

# שמירת הקובץ
tree = ET.ElementTree(root)
tree.write("tv.xml", encoding="utf-8", xml_declaration=True)
print("XMLTV with programs generated successfully via OpenBullet logic!")
