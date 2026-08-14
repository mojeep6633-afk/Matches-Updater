import requests
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import sys

# دعم اللغة العربية
sys.stdout.reconfigure(encoding='utf-8')

# الاتصال بفايربيس
try:
    firebase_key_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if firebase_key_json:
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("firebase_key.json")
        
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("تم الاتصال بفايربيس بنجاح! 🎉")
except Exception as e:
    print(f"تحذير: لم يتم الاتصال بفايربيس: {e}")

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("خطأ: لم يتم العثور على API_KEY")
    sys.exit(1)

# التوقيت
saudi_tz = pytz.timezone('Asia/Riyadh')
now_saudi = datetime.now(saudi_tz)
today_date = now_saudi.strftime('%Y-%m-%d')
last_updated_str = now_saudi.strftime('%Y-%m-%d %I:%M %p')

url_fixtures = "https://v3.football.api-sports.io/fixtures"
querystring = {
    "date": today_date,
    "timezone": "Asia/Riyadh"
}

headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY
}

# قائمة بأرقام الدوريات المطلوبة وأسمائها المنقحة لتظهر بشكل جميل
target_leagues = {
    307: "دوري روشن السعودي",
    311: "كأس خادم الحرمين الشريفين",
    17:  "دوري أبطال آسيا للنخبة",
    3:   "الدوري الأوروبي",
    39:  "الدوري الإنجليزي",
    140: "الدوري الإسباني",
    135: "الدوري الإيطالي",
    61:  "الدوري الفرنسي",
    71:  "الدوري البرازيلي",
    15:  "كأس الخليج العربي", 
    16:  "دوري أبطال الخليج للأندية" # بديل مقارب لمجلس التعاون
}

try:
    print(f"جاري البحث عن مباريات ليوم: {today_date}")
    response = requests.get(url_fixtures, headers=headers, params=querystring)
    data = response.json()
    
    matches_today = data.get("response", [])
    all_matches_list = []

    for match in matches_today:
        league_id = match["league"]["id"]
        
        # فلترة المباريات بناءً على الدوريات المطلوبة فقط
        if league_id in target_leagues:
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            home_logo = match["teams"]["home"]["logo"]
            away_logo = match["teams"]["away"]["logo"]
            
            # تعديل اسم الدوري للاسم العربي المنسق
            league_name = target_leagues.get(league_id)
            
            dt = datetime.fromisoformat(match["fixture"]["date"])
            time_arabic = dt.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
            
            fixture_id = str(match["fixture"]["id"])
            
            # جلب القنوات الناقلة
            url_tv = "https://v3.football.api-sports.io/fixtures/tv"
            tv_response = requests.get(url_tv, headers=headers, params={"fixture": fixture_id}).json()
            tv_data = tv_response.get("response", [])
            
            channel_name = "غير محدد"
            if tv_data:
                channels_list = [tv["tv"]["name"] for tv in tv_data]
                raw_channel = " , ".join(channels_list)
                
                # إحلال "ثمانية الرياضية" مكان القنوات السعودية القديمة
                if league_id in [307, 311]:
                    if "SSC" in raw_channel.upper() or not raw_channel:
                        channel_name = "ثمانية الرياضية"
                    else:
                        channel_name = raw_channel
                else:
                    channel_name = raw_channel

            # تعيين قنوات افتراضية عربية في حال لم يُرجع الـ API اسم القناة
            if channel_name == "غير محدد":
                if league_id in [307, 311]:
                    channel_name = "ثمانية الرياضية"
                elif league_id in [39, 140, 61, 17]:
                    channel_name = "beIN Sports"
                elif league_id == 135:
                    channel_name = "AD Sports"
            
            print(f"المباراة: {home_team} ضد {away_team} | الدوري: {league_name} | القناة: {channel_name}")

            match_dict = {
                "home_team": home_team,
                "home_team_logo": home_logo,
                "away_team": away_team,
                "away_team_logo": away_logo,
                "match_time": time_arabic,
                "league_name": league_name,
                "channels": [
                    {
                        "name": channel_name,
                        "commentator": "غير محدد"
                    }
                ]
            }
            all_matches_list.append(match_dict)

    if len(all_matches_list) == 0:
        print("لم يتم العثور على مباريات لهذه الدوريات اليوم.")
    else:
        if 'db' in locals():
            final_data = {
                "last_updated": last_updated_str,
                "matches": all_matches_list
            }
            db.collection('daily_matches').document('daily_matches').set(final_data)
            print(f"تم رفع {len(all_matches_list)} مباريات لتطبيقك بنجاح! 🚀")

except Exception as e:
    print(f"حدث خطأ: {e}")
