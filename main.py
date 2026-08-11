import json
import os
from datetime import datetime

from bs4 import BeautifulSoup
import firebase_admin
import pytz
import requests
from firebase_admin import credentials, firestore

def get_todays_matches():
    riyadh_tz = pytz.timezone("Asia/Riyadh")
    today_date = datetime.now(riyadh_tz).strftime("%Y-%m-%d")
    
    print(f"بدء جلب المباريات ليوم: {today_date} من موقع في الجول...")
    
    url = "https://www.filgoal.com/matches"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        print(f"حالة الاتصال بالموقع: {response.status_code}")
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        clean_matches = []

        important_leagues = [
            "دوري روشن السعودي", "كأس خادم الحرمين الشريفين", "كاس خادم الحرمين الشريفين",
            "دوري أبطال أوروبا", "دوري ابطال اوروبا", "دوري أبطال آسيا", "دوري ابطال اسيا",
            "الدوري الإنجليزي", "الدوري الانجليزي", "الدوري الإسباني", "الدوري الاسباني",
            "الدوري الإيطالي", "الدوري الايطالي", "مباريات دولية",
            "دوري أبطال آسيا للنخبة", "دوري ابطال اسيا للنخبة", "كأس العالم", "كاس العالم",
            "كأس السوبر", "كاس السوبر", "دوري أبطال إفريقيا", "دوري ابطال افريقيا",
            "دوري يلو", "ودي", "ودية", "مباريات ودية", "ودية أندية"
        ]

        # البحث عن كتل المباريات في هيكلة الموقع الجديدة
        match_blocks = soup.find_all("div", class_="match-block")
        if not match_blocks:
            match_blocks = soup.find_all("div", class_="ic-match")
            
        print(f"عدد كتل المباريات المكتشفة في الصفحة: {len(match_blocks)}")

        for block in match_blocks:
            try:
                champ_elem = block.find("div", class_="champ-name")
                champ_name = champ_elem.get_text(strip=True) if champ_elem else "بطولة غير معروفة"

                is_important = any(league in champ_name for league in important_leagues)
                if not is_important:
                    continue

                home_elem = block.find("div", class_="team-1")
                away_elem = block.find("div", class_="team-2")
                
                home_team = home_elem.get_text(strip=True) if home_elem else "فريق 1"
                away_team = away_elem.get_text(strip=True) if away_elem else "فريق 2"

                time_elem = block.find("div", class_="match-time")
                final_time = time_elem.get_text(strip=True) if time_elem else "محدد"

                channel_elem = block.find("div", class_="channel")
                channel = channel_elem.get_text(strip=True) if channel_elem else "غير متوفر"

                logos = block.find_all("img")
                home_logo = logos[0]["src"] if len(logos) > 0 and "src" in logos[0] else ""
                away_logo = logos[1]["src"] if len(logos) > 1 and "src" in logos[1] else ""

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
            except Exception:
                continue

        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء جلب الصفحة: {e}")
        return None

def update_firebase(matches):
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

    # مسح القديم وكتابة الجديد
    docs = collection_ref.stream()
    for doc in docs:
        doc.reference.delete()

    if matches:
        for match_id, match_data in matches:
            collection_ref.document(str(match_id)).set(match_data)
        print(f"تم رفع {len(matches)} مباراة بنجاح إلى مجموعة koora.")
    else:
        # إضافة وثيقة اختبارية لضمان عمل قاعدة البيانات وعدم بقائها فارغة
        collection_ref.document("test_connection").set({
            "league": "اختبار النظام",
            "homeTeam": "حالة السكربت",
            "awayTeam": "متصل بنجاح",
            "time": "00:00",
            "channelName": "مباشر",
            "homeTeamLogo": "",
            "awayTeamLogo": "",
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print("لم يتم العثور على مباريات مطابقة حالياً، وتم إنشاء وثيقة اختبارية لضمان عمل الاتصال.")

if __name__ == "__main__":
    print("بدء تنفيذ السكربت المباشر...")
    todays_matches = get_todays_matches()
    update_firebase(todays_matches)
