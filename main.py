import json
import os
from datetime import datetime

import firebase_admin
import pytz
import requests
from firebase_admin import credentials, firestore

def get_todays_matches():
    # الاعتماد على توقيت السعودية بشكل صارم (اليوم يبدأ 12:00 ليلاً)
    riyadh_tz = pytz.timezone("Asia/Riyadh")
    now_riyadh = datetime.now(riyadh_tz)
    today_date = now_riyadh.strftime("%Y-%m-%d")
    
    print(f"جاري سحب مباريات تاريخ: {today_date} بتوقيت السعودية...")
    
    url = f"https://api.filgoal.com/api/matches/GetByDate?date={today_date}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
        )
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        matches_data = response.json()

        cairo_tz = pytz.timezone("Africa/Cairo")

        clean_matches = []

        # القائمة المعتمدة مع تنويعات الهمزات
        important_leagues = [
            "دوري روشن السعودي",
            "كأس خادم الحرمين الشريفين", "كاس خادم الحرمين الشريفين",
            "دوري أبطال أوروبا", "دوري ابطال اوروبا",
            "دوري أبطال آسيا", "دوري ابطال اسيا",
            "الدوري الإنجليزي", "الدوري الانجليزي",
            "الدوري الإسباني", "الدوري الاسباني",
            "الدوري الإيطالي", "الدوري الايطالي",
            "مباريات دولية",
            "دوري أبطال آسيا للنخبة", "دوري ابطال اسيا للنخبة",
            "كأس العالم", "كاس العالم",
            "كأس السوبر", "كاس السوبر",
            "دوري أبطال إفريقيا", "دوري ابطال افريقيا",
            "دوري يلو",
            "ودي",
            "ودية",
            "مباريات ودية",
            "ودية أندية",
            "مباريات ودية - أندية"
        ]

        for match in matches_data:
            champ_name = match.get("ChampionshipName", "بطولة غير معروفة")
            home_team = match.get("HomeTeamName", "فريق 1")
            away_team = match.get("AwayTeamName", "فريق 2")

            is_important_league = any(league in champ_name for league in important_leagues)
            
            if not is_important_league:
                # هذه الرسالة ستظهر في جيت هاب لتعرف لماذا تم تجاهل المباراة
                print(f"تم تجاهل: {champ_name} ({home_team} ضد {away_team})")
                continue

            print(f"تم اعتماد: {champ_name} ({home_team} ضد {away_team})")

            home_logo = match.get("HomeTeamLogoUrl", "")
            if home_logo and not home_logo.startswith("http"):
                home_logo = f"https://www.filgoal.com{home_logo}"

            away_logo = match.get("AwayTeamLogoUrl", "")
            if away_logo and not away_logo.startswith("http"):
                away_logo = f"https://www.filgoal.com{away_logo}"

            channel = match.get("ChannelName", "غير متوفر")

            match_date_str = match.get("Date")
            if match_date_str:
                match_time_obj = datetime.strptime(
                    match_date_str[:19], "%Y-%m-%dT%H:%M:%S"
                )
                match_time_cairo = cairo_tz.localize(match_time_obj)
                local_match_time = match_time_cairo.astimezone(riyadh_tz)
                final_time = local_match_time.strftime("%H:%M")
            else:
                final_time = "غير محدد"

            match_id = f"{home_team}_{away_team}".replace(" ", "_")

            clean_matches.append(
                (
                    match_id,
                    {
                        "league": champ_name,
                        "homeTeam": home_team,
                        "awayTeam": away_team,
                        "time": final_time,
                        "channelName": channel,
                        "homeTeamLogo": home_logo,
                        "awayTeamLogo": away_logo,
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
        print("لا توجد مباريات مهمة اليوم (حسب القائمة المعتمدة).")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_cert_string:
        print("خطأ: لم يتم العثور على مفتاح فايربيس السري في إعدادات جيت هاب")
        return

    firebase_cert = json.loads(firebase_cert_string)
    cred = credentials.Certificate(firebase_cert)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    collection_ref = db.collection("daily_matches")

    docs = collection_ref.stream()
    for doc in docs:
        doc.reference.delete()

    for match_id, match_data in matches:
        collection_ref.document(str(match_id)).set(match_data)

    print(f"تم تحديث فايربيس بنجاح بـ {len(matches)} مباراة مهمة!")

if __name__ == "__main__":
    print("بدأ سحب وتجهيز جدول المباريات...")
    todays_matches = get_todays_matches()
    update_firebase(todays_matches)
