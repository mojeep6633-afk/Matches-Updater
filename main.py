import json
import os
from datetime import datetime
import firebase_admin
import pytz
import requests
from firebase_admin import credentials, firestore

def get_todays_matches():
    today_date = datetime.now().strftime("%Y-%m-%d")
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
        riyadh_tz = pytz.timezone("Asia/Riyadh")

        clean_matches = []

        important_leagues = [
            "دوري روشن السعودي", "دوري أبطال أوروبا", "دوري أبطال آسيا",
            "الدوري الإنجليزي", "الدوري الإسباني", "الدوري الإيطالي",
            "مباريات دولية", "دوري أبطال آسيا للنخبة", "كأس العالم",
            "دوري أبطال إفريقيا", "ودي", "ودية", "مباريات ودية",
            "ودية أندية", "مباريات ودية - أندية"
        ]

        for match in matches_data:
            champ_name = match.get("ChampionshipName", "بطولة غير معروفة")

            if not any(league in champ_name for league in important_leagues):
                continue

            home_team = match.get("HomeTeamName", "فريق 1")
            away_team = match.get("AwayTeamName", "فريق 2")

            home_logo = match.get("HomeTeamLogoUrl", "")
            if home_logo and not home_logo.startswith("http"):
                home_logo = f"https://www.filgoal.com{home_logo}"

            away_logo = match.get("AwayTeamLogoUrl", "")
            if away_logo and not away_logo.startswith("http"):
                away_logo = f"https://www.filgoal.com{away_logo}"

            channel = match.get("ChannelName", "غير متوفر")

            match_date_str = match.get("Date")
            if match_date_str:
                match_time_obj = datetime.strptime(match_date_str[:19], "%Y-%m-%dT%H:%M:%S")
                match_time_cairo = cairo_tz.localize(match_time_obj)
                local_match_time = match_time_cairo.astimezone(riyadh_tz)
                # صيغة الوقت التي يتوقعها التطبيق (تحتوي على T وزائد)
                final_time = local_match_time.strftime("%Y-%m-%dT%H:%M:%S+03:00") 
            else:
                final_time = ""

            # هيكلة البيانات لتتطابق تماماً مع ما يتوقعه تطبيق الأندرويد
            clean_matches.append({
                "league_name": champ_name,
                "home_team": home_team,
                "away_team": away_team,
                "match_time": final_time,
                "home_team_logo": home_logo,
                "away_team_logo": away_logo,
                "channels": [
                    {
                        "name": channel,
                        "commentator": "" # موقع الجول لا يوفر معلقين عادةً، نتركها فارغة
                    }
                ]
            })

        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None


def update_firebase(matches_list):
    if not matches_list:
        print("لا توجد مباريات مهمة اليوم أو حدث خطأ.")
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
    
    # 🔴 هذا هو السطر الحاسم الذي يضع البيانات في المصفوفة "matches"
    doc_ref = db.collection("koora").document("daily_matches")
    doc_ref.set({"matches": matches_list})

    print(f"تم تحديث فايربيس بنجاح بـ {len(matches_list)} مباراة مهمة!")


if __name__ == "__main__":
    print("بدأ سحب وتجهيز جدول المباريات...")
    todays_matches = get_todays_matches()
    update_firebase(todays_matches)
