import json
import os
from datetime import datetime

import firebase_admin
import pytz
import requests
from firebase_admin import credentials, firestore

def get_todays_matches():
    riyadh_tz = pytz.timezone("Asia/Riyadh")
    today_date = datetime.now(riyadh_tz).strftime("%Y-%m-%d")
    
    print(f"جاري جلب جدول مباريات اليوم: {today_date} من المصدر البديل والمستقر...")
    
    # استخدام مصدر API موثوق وثابت لجدول المباريات اليومية
    url = f"https://www.scorebat.com/video-api/v3/"

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        match_list = data.get("response", [])

        clean_matches = []
        
        # البطولات والدوريات المحددة التي طلبتها فقط
        important_leagues = [
            "Saudi Professional League", "Saudi Crown Prince Cup", "King Cup",
            "UEFA Champions League", "AFC Champions League", "AFC Champions League Elite",
            "Premier League", "La Liga", "Serie A", "Ligue 1", "Bundesliga",
            "World Cup", "Super Cup", "CAF Champions League", "Saudi First Division", "Friendly"
        ]

        for match in match_list:
            competition = match.get("competition", "")
            
            # التحقق من مطابقة البطولات
            is_matched = any(league.lower() in competition.lower() for league in important_leagues)
            if not is_matched:
                continue

            title = match.get("title", "")
            date_str = match.get("date", "")
            thumbnail = match.get("thumbnail", "")
            videos = match.get("videos", [])
            channel = videos[0].get("title", "مباشر") if videos else "غير متوفر"

            # استخراج الوقت وتنسيقه بتوقيت السعودية
            try:
                dt_obj = datetime.strptime(date_str[:19], "%Y-%m-%dT%H:%M:%S")
                match_time = dt_obj.strftime("%H:%M")
            except:
                match_time = "محدد"

            teams = title.split(" - ")
            home_team = teams[0].strip() if len(teams) > 0 else "فريق 1"
            away_team = teams[1].strip() if len(teams) > 1 else "فريق 2"

            match_id = f"{home_team}_{away_team}".replace(" ", "_")

            clean_matches.append(
                (
                    match_id,
                    {
                        "league": competition,
                        "homeTeam": home_team,
                        "awayTeam": away_team,
                        "time": match_time,
                        "channelName": channel,
                        "homeTeamLogo": thumbnail,
                        "awayTeamLogo": "",
                        "timestamp": firestore.SERVER_TIMESTAMP,
                    },
                )
            )

        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

def update_firebase(matches):
    if not matches:
        print("لا توجد مباريات مطابقة للدوريات المحددة اليوم.")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_cert_string:
        print("خطأ: مفتاح فايربيس غير موجود في إعدادات جيت هاب")
        return

    firebase_cert = json.loads(firebase_cert_string)
    cred = credentials.Certificate(firebase_cert)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    collection_ref = db.collection("koora")

    # تثبيت الجدول لليوم بالكامل دفعة واحدة
    for match_id, match_data in matches:
        collection_ref.document(str(match_id)).set(match_data)

    print(f"تم تثبيت {len(matches)} مباراة بنجاح داخل مجموعة koora في فايربيس!")

if __name__ == "__main__":
    print("بدء عملية التحديث الجذري...")
    todays_matches = get_todays_matches()
    update_firebase(todays_matches)
