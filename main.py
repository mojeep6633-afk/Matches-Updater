import os
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pytz

def fetch_matches():
    api_key = os.environ.get("API_SPORTS_KEY")
    if not api_key:
        print("خطأ: مفتاح API-Sports غير موجود")
        return []

    tz = pytz.timezone('Asia/Riyadh')
    today = datetime.now(tz).strftime("%Y-%m-%d")

    url = "https://v3.football.api-sports.io/fixtures"
    
    # طلب كل مباريات اليوم بدون تحديد دوري معين
    querystring = {"date": today}

    headers = {
        "x-apisports-key": api_key
    }

    # قائمة بأرقام البطولات التي تهمك
    target_leagues = [307, 308, 310, 2, 17, 18, 39, 140, 135, 12, 1, 66]
    
    matches_list = []
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get("response", [])
            
            for item in fixtures:
                league_id = item["league"]["id"]
                
                # التحقق مما إذا كانت المباراة ضمن بطولاتنا المطلوبة
                if league_id in target_leagues:
                    match_data = {
                        "league_name": item["league"]["name"],
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
