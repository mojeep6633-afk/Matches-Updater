import json
import os
from datetime import datetime
from apify_client import ApifyClient
import firebase_admin
from firebase_admin import credentials, firestore

def get_365scores_matches():
    APIFY_TOKEN = "apify_api_yJ5YPMy0T1ecpOB21nFMhUzffI7HYL2P41nU"
    client = ApifyClient(APIFY_TOKEN)

    actor_id = "crawlergang/365scores-scraper"

    # تصحيح القيم لتتوافق مع القيم المسموحة في الأداة حصرياً
    run_input = {
        "mode": "liveScores",
        "sport": "football",
        "maxItems": 150
    }

    print("جاري تشغيل كاشف 365Scores عبر الأداة الخاصة بك...")

    try:
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list().items
        
        target_leagues = [
            "Saudi", "Saudi Professional", "King", "Cup", 
            "AFC", "Champions League", "Europa", 
            "Premier League", "La Liga", "Serie A", 
            "Ligue 1", "Brasileiro", "Gulf", "الدوري السعودي", "كأس الملك"
        ]
        
        clean_matches = []
        for match in dataset_items:
            league = match.get("competition", "") or match.get("competitionName", "") or match.get("league", "")
            
            if any(target.lower() in league.lower() for target in target_leagues):
                if "Friendly" in league or "ودية" in league:
                    continue
                
                clean_matches.append({
                    "league_name": league,
                    "home_team": match.get("homeTeam", "") or match.get("homeTeamName", ""),
                    "away_team": match.get("awayTeam", "") or match.get("awayTeamName", ""),
                    "match_time": match.get("gameTime", "") or match.get("time", "توقيت غير محدد"),
                    "home_team_logo": match.get("homeTeamImageUrl", "") or match.get("homeLogo", ""),
                    "away_team_logo": match.get("awayTeamImageUrl", "") or match.get("awayLogo", ""),
                    "status": match.get("statusText", "مجدولة"),
                    "channels": [{"name": "قنوات النقل الرسمية", "commentator": "غير محدد"}]
                })
            
        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء سحب البيانات من Apify: {e}")
        return []

def update_firebase(matches_list):
    if not matches_list:
        print("مصفوفة المباريات فارغة أو لا توجد مباريات مطابقة للبطولات المطلوبة اليوم.")
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
        doc_ref = db.collection("koora").document("daily_matches")
        doc_ref.set({"matches": matches_list, "last_updated": datetime.now().isoformat()})
        print(f"✅ تم تحديث {len(matches_list)} مباراة بنجاح في الفايربيس!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_365scores_matches()
    update_firebase(data)
