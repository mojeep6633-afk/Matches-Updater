import json
import os
from datetime import datetime
import requests
import firebase_admin
from firebase_admin import credentials, firestore

# قائمة البطولات المطلوبة بالمعرفات أو الكلمات المفتاحية للفلترة
TARGET_LEAGUES = [
    "Saudi Professional League",
    "King Cup",
    "AFC Champions League",
    "UEFA Champions League",
    "UEFA Europa League",
    "Premier League",
    "La Liga",
    "Serie A",
    "Ligue 1",
    "Brasileirão"
]

def get_matches_from_api():
    print("جاري جلب جدول المباريات للبطولات المحددة...")
    clean_matches = []
    
    try:
        # استخدام مصدر رياضي موثوق ومفتوح لجلب المباريات المباشرة
        url = "https://www.thesportsdb.com/api/v1/json/3/eventsday.php?d=" + datetime.now().strftime("%Y-%m-%d")
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            events = data.get("events", [])
            
            if events:
                for ev in events:
                    league = ev.get("strLeague", "")
                    
                    # فلترة المباريات لتشمل فقط ما طلبته
                    if any(target.lower() in league.lower() for target in TARGET_LEAGUES):
                        clean_matches.append({
                            "league_name": league,
                            "home_team": ev.get("strHomeTeam", ""),
                            "away_team": ev.get("strAwayTeam", ""),
                            "match_time": ev.get("strTime", "توقيت غير محدد"),
                            "home_team_logo": ev.get("strHomeTeamBadge", ""),
                            "away_team_logo": ev.get("strAwayTeamBadge", ""),
                            "status": ev.get("strStatus", "مجدولة"),
                            "channels": [{"name": ev.get("strTVStation", "غير متوفر"), "commentator": "غير محدد"}]
                        })
                        
        return clean_matches
    except Exception as e:
        print(f"خطأ في السحب: {e}")
        return []

def update_firebase(matches_list):
    if not matches_list:
        print("لا توجد مباريات مطابقة للبطولات المطلوبة اليوم.")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    try:
        if firebase_cert_string:
            firebase_cert = json.loads(firebase_cert_string)
            cred = credentials.Certificate(firebase_cert)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
            
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        db.collection("koora").document("daily_matches").set(
            {"matches": matches_list, "last_updated": datetime.now().isoformat()}
        )
        print(f"🔥 تم تحديث {len(matches_list)} مباراة بنجاح في الفايربيس!")
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    matches = get_matches_from_api()
    update_firebase(matches)
