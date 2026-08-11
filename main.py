import os
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pytz

def fetch_matches():
    # استدعاء مفتاح الـ API من جيت هاب
    api_key = os.environ.get("API_SPORTS_KEY")
    if not api_key:
        print("خطأ: مفتاح API-Sports غير موجود")
        return []

    tz = pytz.timezone('Asia/Riyadh')
    today = datetime.now(tz).strftime("%Y-%m-%d")

    # الرابط الرسمي المباشر لـ API-Sports
    url = "https://v3.football.api-sports.io/fixtures"
    
    # 307 = دوري روشن، 2026 = الموسم
    querystring = {"date": today, "league": "307", "season": "2026"}

    headers = {
        "x-apisports-key": api_key
    }

    matches_list = []
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get("response", [])
            
            for item in fixtures:
                match_data = {
                    "home_team": item["teams"]["home"]["name"],
                    "away_team": item["teams"]["away"]["name"],
                    "status": item["fixture"]["status"]["long"],
                    "goals_home": item["goals"]["home"],
                    "goals_away": item["goals"]["away"],
                    "match_time": item["fixture"]["date"]
                }
                matches_list.append(match_data)
    except Exception as e:
        print(f"حدث خطأ أثناء جلب المباريات: {e}")
        
    return matches_list

def update_firebase(matches):
    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_cert_string:
        print("خطأ: مفتاح فايربيس غير موجود")
        return

    try:
        firebase_cert = json.loads(firebase_cert_string)
        cred = credentials.Certificate(firebase_cert)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        
        db.collection("koora").document("daily_matches").set({
            "matches": matches,
            "last_update": firestore.SERVER_TIMESTAMP
        })
        print(f"تم حفظ وتحديث {len(matches)} مباريات بنجاح!")
        
    except Exception as e:
        print(f"فشل الاتصال بفايربيس: {e}")

if __name__ == "__main__":
    print("جاري جلب المباريات...")
    matches_data = fetch_matches()
    update_firebase(matches_data)
