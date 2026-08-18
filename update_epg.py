from datetime import datetime
import json
import requests
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

def format_hot_time(time_str: str) -> str:
    try:
        if not time_str or not time_str.strip():
            return ''
        dt_local = datetime.strptime(time_str.strip(), '%Y/%m/%d %H:%M:%S')
        dt_israel = dt_local.replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
        dt_utc = dt_israel.astimezone(ZoneInfo('UTC'))
        return dt_utc.strftime('%Y%m%d%H%M%S +0000')
    except Exception as e:
        print(f"שגיאת המרת זמן עבור '{time_str}': {e}")
        return ''.join(filter(str.isdigit, time_str))[:14] + ' +0000'

def fetch_hot_epg():
    today = datetime.now()
    start_date_str = today.strftime('%Y/%m/%d 00:00:00')
    end_date_str = (
        datetime.now()
        .replace(hour=23, minute=59, second=59)
        .fromordinal(today.toordinal() + 5)
        .strftime('%Y/%m/%d 23:59:59')
    )

    url = 'https://www.hot.net.il/HotCmsApiFront/api/ProgramsSchedual/GetProgramsSchedual'
    payload = {
        'ProgramsStartDateTime': start_date_str,
        'ProgramsEndDateTime': end_date_str,
    }

    # שימוש ב-Session לשמירה על העוגיות והגדרות הבקשה
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
        'Content-Type': 'application/json',
        'Origin': 'https://www.hot.net.il',
        'Referer': 'https://www.hot.net.il/heb/tv/tvguide/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
    })

    tv = ET.Element('tv')
    target_channels = ['127', '215', '151']

    for channel_id in target_channels:
        channel_elem = ET.SubElement(tv, 'channel', id=channel_id)
        display_name = ET.SubElement(channel_elem, 'display-name')
        display_name.text = f'Channel {channel_id}'

    print(f'מתחיל הורדת לוח שידורים לטווח: {start_date_str} עד {end_date_str}')

    try:
        # טעינה ראשונית של דף הבית לקבלת עוגיות (Session Cookies)
        session.get('https://www.hot.net.il/heb/tv/tvguide/', timeout=15)

        # ביצוע בקשת ה-POST ללא מעקב אוטומטי אחר הפניות אינסופיות
        response = session.post(url, json=payload, timeout=30, allow_redirects=False)
        print(f'סטטוס תגובה מהשרת: {response.status_code}')

        # אם התקבלה הפנייה (301/302), נדפיס לאן השרת מנסה להפנות
        if response.status_code in (301, 302, 307, 308):
            print(f"השרת החזיר הפנייה לכתובת: {response.headers.get('Location')}")
            # ניסיון פנייה ישיר לכתובת ההפנייה במידת הצורך
            response = session.post(response.headers.get('Location'), json=payload, timeout=30)

        if response.status_code == 200:
            res_json = response.json()
            if isinstance(res_json, dict) and 'data' in res_json and res_json['data'] and 'programsDetails' in res_json['data']:
                programs_list = res_json['data']['programsDetails']
            elif isinstance(res_json, list):
                programs_list = res_json
            else:
                programs_list = []

            print(f'סך הכל פריטים שהתקבלו מהשרת: {len(programs_list)}')

            for channel_id in target_channels:
                match_count = 0
                for item in programs_list:
                    if str(item.get('channelID', '')) == channel_id:
                        title = item.get('programTitle', '').strip()
                        raw_desc = item.get('synopsis', '').strip()
                        desc = (raw_desc[:80].strip() + '...') if len(raw_desc) > 80 else raw_desc.strip()

                        raw_start = item.get('programStartTime', '')
                        raw_end = item.get('programEndTime', '')

                        start_time = format_hot_time(raw_start)
                        end_time = format_hot_time(raw_end)

                        if channel_id in ['127', '215']:
                            episode = str(item.get('programEpisode', '')).strip()
                            full_title = f'{title} - פרק {episode}' if episode and episode != '0' else title
                        else:
                            full_title = title

                        if full_title and start_time and end_time:
                            match_count += 1
                            prog_elem = ET.SubElement(tv, 'programme', start=start_time, stop=end_time, channel=channel_id)
                            title_elem = ET.SubElement(prog_elem, 'title', lang="he")
                            title_elem.text = full_title
                            if desc:
                                desc_elem = ET.SubElement(prog_elem, 'desc', lang="he")
                                desc_elem.text = desc

                print(f'נמצאו תוכניות לערוץ {channel_id}: {match_count}')
        else:
            print(f'שגיאה מהשרת ({response.status_code}): {response.text[:200]}')

    except Exception as e:
        print(f'שגיאה במהלך הדרישה מהשרת: {e}')

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="\t", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("קובץ epg.xml נשמר בהצלחה!")

if __name__ == '__main__':
    fetch_hot_epg()
