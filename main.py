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

# التوقيت الدقيق بواسطة بايثون
saudi_tz = pytz.timezone('Asia/Riyadh')
now_saudi = datetime.now(saudi_tz)
today_date_saudi = now_saudi.strftime('%Y-%m-%d')
last_updated_str = now_saudi.strftime('%Y-%m-%d %I:%M %p')

# سر المشكلة كان هنا: أزلنا "timezone" من الطلب لنتجنب خطأ السيرفر بعد منتصف الليل
url_fixtures = "https://v3.football.api-sports.io/fixtures"
querystring = {
    "date": today_date_saudi
}

headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY
}

target_leagues_names = {
    307: "الدوري السعودي للمحترفين",
    311: "كأس خادم الحرمين الشريفين",
    17:  "دوري أبطال آسيا للنخبة",
    3:   "الدوري الأوروبي",
    39:  "الدوري الإنجليزي",
    140: "الدوري الإسباني",
    135: "الدوري الإيطالي",
    61:  "الدوري الفرنسي",
    71:  "الدوري البرازيلي",
    15:  "كأس الخليج العربي", 
    16:  "دوري أبطال الخليج للأندية"
}

try:
    print(f"جاري البحث عن مباريات اليوم: {today_date_saudi}")
    response = requests.get(url_fixtures, headers=headers, params=querystring)
    data = response.json()
    
    if "errors" in data and data["errors"]:
        print(f"أخطاء من الـ API: {data['errors']}")
        
    matches_today = data.get("response", [])
    print(f"عدد مباريات العالم المسترجعة من السيرفر: {len(matches_today)}")
    
    all_matches_list = []

    for match in matches_today:
        league_id = match["league"]["id"]
        
        # فلترة مبدئية للدوريات المطلوبة
        if league_id in target_leagues_names:
            
            # التحويل الدقيق لتوقيت السعودية لضمان عدم ضياع أي مباراة
            utc_dt = datetime.fromisoformat(match["fixture"]["date"].replace('Z', '+00:00'))
            saudi_dt = utc_dt.astimezone(saudi_tz)
            match_date_saudi = saudi_dt.strftime('%Y-%m-%d')
            
            # التأكد أن المباراة تُلعب "اليوم" فعلياً بتوقيت السعودية
            if match_date_saudi == today_date_saudi:
                league_name_api = match["league"]["name"]
                league_name = target_leagues_names.get(league_id, league_name_api)

                home_team = match["teams"]["home"]["name"]
                away_team = match["teams"]["away"]["name"]
                home_logo = match["teams"]["home"]["logo"]
                away_logo = match["teams"]["away"]["logo"]
                
                time_arabic = saudi_dt.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
                fixture_id = str(match["fixture"]["id"])
                
                channel_name = "غير محدد"
                
                # جلب القنوات الناقلة
                url_tv = "https://v3.football.api-sports.io/fixtures/tv"
                tv_response = requests.get(url_tv, headers=headers, params={"fixture": fixture_id}).json()
                tv_data = tv_response.get("response", [])
                
                if tv_data:
                    channels_list = [tv["tv"]["name"] for tv in tv_data]
                    raw_channel = " , ".join(channels_list)
                    
                    # استبدال ذكي: تحويل كلمة SSC إلى ثمانية مع الحفاظ على الأرقام
                    if league_id in [307, 311]:
                        channel_name = raw_channel.replace("SSC", "ثمانية").replace("ssc", "ثمانية").replace("Ssc", "ثمانية")
                    else:
                        channel_name = raw_channel

                # قنوات افتراضية أوروبية فقط (وليس للسعودي)
                if channel_name == "غير محدد":
                    if league_id in [39, 140, 61, 17]:
                        channel_name = "beIN Sports"
                    elif league_id == 135:
                        channel_name = "AD Sports"

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
                print(f"تمت الإضافة: {home_team} ضد {away_team} | الساعة {time_arabic} | القناة: {channel_name}")

    if len(all_matches_list) == 0:
        print("لم يتم العثور على مباريات لدورياتك هذا اليوم.")
    else:
        if 'db' in locals():
            final_data = {
                "last_updated": last_updated_str,
                "matches": all_matches_list
            }
            db.collection('daily_matches').document('daily_matches').set(final_data)
            print(f"تم رفع {len(all_matches_list)} مباراة لتطبيقك بنجاح! 🚀")

except Exception as e:
    print(f"حدث خطأ: {e}")
