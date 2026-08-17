from datetime import datetime
import json
import requests
from zoneinfo import ZoneInfo  # מובנה בפייתון מגרסה 3.9 ומעלה


def format_hot_time(time_str: str) -> str:
  try:
    if not time_str or not time_str.strip():
      return ''
    # המרת הזמן המקומי של ישראל ל־UTC בהתאם ללוגיקה שקיימת בקוטלין
    dt_local = datetime.strptime(time_str.strip(), '%Y/%m/%d %H:%M:%S')
    dt_israel = dt_local.replace(tzinfo=ZoneInfo('Asia/Jerusalem'))
    dt_utc = dt_israel.astimezone(ZoneInfo('UTC'))
    return dt_utc.strftime('%Y%m%d%H%M%S')
  except Exception as e:
    print(f"שגיאת המרת זמן עבור '{time_str}': {e}")
    return ''.join(filter(str.isdigit, time_str))[:14]


def fetch_hot_epg():
  # הגדרת תאריכים בדיוק כמו בקוד של אנדרואיד (היום + 5 קדימה)
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

  headers = {
      'Host': 'www.hot.net.il',
      'Origin': 'https://www.hot.net.il',
      'Referer': 'https://www.hot.net.il/heb/tv/tvguide/',
      'Content-Type': 'application/json',
      'Accept': 'application/json, text/plain, */*',
      'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
      'User-Agent': (
          'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,'
          ' like Gecko) Chrome/151.0.0.0 Safari/537.36'
      ),
  }

  print(f'מתחיל הורדת לוח שידורים לטווח: {start_date_str} עד {end_date_str}')

  try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f'סטטוס תגובה מהשרת: {response.status_code}')

    if response.status_code != 200:
      print('תוכן התגובה החריגה:', response.text[:300])
      return

    res_json = response.json()

    if (
        isinstance(res_json, dict)
        and 'data' in res_json
        and res_json['data']
        and 'programsDetails' in res_json['data']
    ):
      programs_list = res_json['data']['programsDetails']
    elif isinstance(res_json, list):
      programs_list = res_json
    else:
      programs_list = res_json

    print(f'סך הכל פריטים שהתקבלו מהשרת: {len(programs_list)}')

    target_channels = ['127', '215', '151']

    for channel_id in target_channels:
      match_count = 0
      print(f'\n--- בדיקת ערוץ ID: {channel_id} ---')

      for item in programs_list:
        if str(item.get('channelID', '')) == channel_id:
          title = item.get('programTitle', '').strip()
          raw_desc = item.get('synopsis', '').strip()
          desc = (
              (raw_desc[:80].strip() + '...')
              if len(raw_desc) > 80
              else raw_desc.strip()
          )

          raw_start = item.get('programStartTime', '')
          raw_end = item.get('programEndTime', '')

          start_time = format_hot_time(raw_start)
          end_time = format_hot_time(raw_end)

          if channel_id in ['127', '215']:
            episode = str(item.get('programEpisode', '')).strip()
            if episode and episode != '0':
              full_title = f'{title} - פרק {episode}'
            else:
              full_title = title
          else:
            full_title = title

          if full_title and start_time and end_time:
            match_count += 1
            if match_count <= 3:
              print(
                  f"  תוכנית [{match_count}]: '{full_title}' | התחלה:"
                  f' {start_time} | סיום: {end_time}'
              )

      print(f'נמצאו תוכניות לערוץ {channel_id}: {match_count}')

  except Exception as e:
    print(f'שגיאה בתהליך: {e}')


if __name__ == '__main__':
  fetch_hot_epg()
