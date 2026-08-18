from datetime import datetime
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright

def format_hot_time(time_str: str) -> str:
    try:
        if not time_str or not time_str.strip():
            return ''
        dt_local = datetime.strptime(time_str.strip(), '%Y/%m/%d %H:%M:%S')
        dt_israel = dt_local.replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
        dt_utc = dt_israel.astimezone(ZoneInfo('UTC'))
        return dt_utc.strftime('%Y%m%d%H%M%S +0000')
    except Exception as e:
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

    tv = ET.Element('tv')
    target_channels = ['127', '215', '151']

    for channel_id in target_channels:
        channel_elem = ET.SubElement(tv, 'channel', id=channel_id)
        display_name = ET.SubElement(channel_elem, 'display-name')
        display_name.text = f'Channel {channel_id}'

    print(f'מתחיל הורדת לוח שידורים לטווח: {start_date_str} עד {end_date_str}')

    try:
        with sync_playwright() as p:
            # פנייה ישירה ל-API ללא טעינת עמוד הדפדפן
            request_context = p.request.new_context(
                extra_http_headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': 'https://www.hot.net.il/heb/tv/tvguide/',
                    'Origin': 'https://www.hot.net.il',
                    'Accept': 'application/json, text/plain, */*',
                    'Content-Type': 'application/json;charset=UTF-8'
                }
            )

            response = request_context.post(url, data=payload)
            print(f'סטטוס תגובה מהשרת: {response.status}')

            if response.status == 200:
                res_json = response.json()
                programs_list = res_json.get('data', {}).get('programsDetails', []) if isinstance(res_json, dict) else res_json

                print(f'סך הכל פריטים שהתקבלו: {len(programs_list)}')

                for channel_id in target_channels:
                    match_count = 0
                    for item in programs_list:
                        if str(item.get('channelID', '')) == channel_id:
                            title = item.get('programTitle', '').strip()
                            raw_desc = item.get('synopsis', '').strip()
                            desc = (raw_desc[:80].strip() + '...') if len(raw_desc) > 80 else raw_desc.strip()

                            start_time = format_hot_time(item.get('programStartTime', ''))
                            end_time = format_hot_time(item.get('programEndTime', ''))

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
                print(f'שגיאה מהשרת ({response.status}): {response.text()[:200]}')

            request_context.dispose()

    except Exception as e:
        print(f'שגיאה במהלך ההורדה: {e}')

    tree = ET.ElementTree(tv)
    ET.indent(tree, space="\t", level=0)
    tree.write("epg.xml", encoding="utf-8", xml_declaration=True)
    print("קובץ epg.xml נשמר בהצלחה!")

if __name__ == '__main__':
    fetch_hot_epg()
