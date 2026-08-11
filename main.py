import os
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
import pytz

def get_default_channels(league_id):
    # تحديد القنوات الناقلة الحقيقية بناءً على رقم البطولة لتتطابق مع سيرفرك
    if league_id in [307, 308, 310]: # البطولات السعودية (دوري روشن، الكأس، السوبر)
        return [{"name": "SSC Sport 1", "commentator": "فهد العتيبي"}, {"name": "SSC Sport 5", "commentator": "عيسى الحربين"}]
    elif league_id in [17, 18]: # دوري أبطال آسيا والنخبة
        return [{"name": "SSC Sport 1", "commentator": "فهد العتيبي"}, {"name": "BeIN Sports AFC", "commentator": "عصام الشوالي"}]
    elif league_id == 2: # دوري أبطال أوروبا
        return [{"name": "BeIN Sports 1", "commentator": "عصام الشوالي"}]
    elif league_id == 39: # الدوري الإنجليزي
        return [{"name": "BeIN Sports 1", "commentator": "حفيظ دراجي"}]
    elif league_id == 140: # الدوري الإسباني
        return [{"name": "BeIN Sports 3", "commentator": "حسن العيدروس"}]
    elif league_id == 135: # الدوري الإيطالي
        return [{"name": "AD Sports 1", "commentator": "فارس عوض"}]
    else:
        return [{"name": "BeIN Sports 1", "commentator": ""}]

def fetch_matches():
    api_key = os.environ.get("API_SPORTS_KEY")
    if not api_key:
        print("خطأ: مفتاح API-Sports غير موجود")
        return []

    tz = pytz.timezone('Asia/Riyadh')
    today = datetime.now(tz).strftime("%Y-%m-%d")

    url = "https://v3.football.api-sports.io/fixtures"
    
    querystring = {"date": today}

    headers = {
        "x-apisports-key": api_key
    }

    target_leagues = [307, 308, 310, 2, 17, 18, 39, 140, 135, 12, 1, 66]
    
    matches_list = []
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            fixtures = data.get("response", [])
            
            for item in fixtures:
                league_id = item["league"]["id"]
                
                if league_id in target_leagues:
                    match_data = {
                        "league_name": item["league"]["name"],
                        "home_team": item["teams"]["home"]["name"],
                        "away_team": item["teams"]["away"]["name"],
                        "home_team_logo": item["teams"]["home"]["logo"],
                        "away_team_logo": item["teams"]["away"]["logo"],
                        "status": item["fixture"]["status"]["long"],
                        "goals_home": item["goals"]["home"],
                        "goals_away": item["goals"]["away"],
                        "match_time": item["fixture"]["date"],
                        "channels": get_default_channels(league_id)
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
