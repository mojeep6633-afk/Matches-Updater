import requests
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import sys

# 1. دعم اللغة العربية
sys.stdout.reconfigure(encoding='utf-8')

# 2. الاتصال بفايربيس
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

# 3. التوقيت
saudi_tz = pytz.timezone('Asia/Riyadh')
now_saudi = datetime.now(saudi_tz)
today_date = now_saudi.strftime('%Y-%m-%d')
last_updated_str = now_saudi.strftime('%Y-%m-%d %I:%M %p') # لتحديث حقل last_updated في تطبيقك

url_fixtures = "https://v3.football.api-sports.io/fixtures"
querystring = {
    "league": "307", 
    "season": "2026", 
    "date": today_date,
    "timezone": "Asia/Riyadh"
}

headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY
}

# 4. جلب وترتيب البيانات لتطابق تطبيق تيتانيوم
try:
    print(f"جاري البحث عن مباريات ليوم: {today_date}")
    response = requests.get(url_fixtures, headers=headers, params=querystring)
    data = response.json()
    
    matches_today = data.get("response", [])
    all_matches_list = [] # سنجمع المباريات هنا في مصفوفة (Array)
    
    if len(matches_today) == 0:
        print("لا يوجد مباريات اليوم.")
    else:
        for match in matches_today:
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            home_logo = match["teams"]["home"]["logo"]
            away_logo = match["teams"]["away"]["logo"]
            league_name = match["league"]["name"]
            
            dt = datetime.fromisoformat(match["fixture"]["date"])
            time_arabic = dt.strftime("%I:%M %p").replace("AM", "ص").replace("PM", "م")
            
            fixture_id = str(match["fixture"]["id"])
            url_tv = "https://v3.football.api-sports.io/fixtures/tv"
            tv_response = requests.get(url_tv, headers=headers, params={"fixture": fixture_id}).json()
            tv_data = tv_response.get("response", [])
            
            channel_name = "ثمانية الرياضية"
            if tv_data:
                channels_list = [tv["tv"]["name"] for tv in tv_data]
                raw_channel = " , ".join(channels_list)
                if "SSC" not in raw_channel.upper():
                    channel_name = raw_channel

            print(f"المباراة: {home_team} ضد {away_team} | القناة: {channel_name}")

            # بناء القاموس (Map) الخاص بكل مباراة بنفس أسماء حقول تطبيقك بالضبط
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

    # 5. الرفع لفايربيس بشكل المصفوفة النهائي
    if 'db' in locals():
        final_data = {
            "last_updated": last_updated_str,
            "matches": all_matches_list
        }
        
        # 🚨 ملاحظة مهمة جداً: تأكد من اسم الكولكشن الأساسي!
        # بناء على صورتك، اسم المستند هو daily_matches
        # الكود بالأسفل يفترض أن اسم الكولكشن أيضاً daily_matches. 
        # إذا كان مختلفاً (مثلاً اسمه Matches)، قم بتغيير الكلمة الأولى فقط في السطر بالأسفل.
        db.collection('daily_matches').document('daily_matches').set(final_data)
        
        print("تم رفع البيانات بالتنسيق المطلوب لتطبيقك بنجاح!")

except Exception as e:
    print(f"حدث خطأ: {e}")
