import json
import os
from datetime import datetime
from apify_client import ApifyClient
import firebase_admin
from firebase_admin import credentials, firestore

def get_365scores_matches():
    APIFY_TOKEN = "apify_api_yJ5YPMy0T1ecpOB21nFMhUzffI7HYL2P41nU"
    client = ApifyClient(APIFY_TOKEN)

    actor_id = "crawlerbros/365scores-scraper"

    run_input = {
        "mode": "liveScores",
        "sport": "football",
        "maxItems": 150
    }

    print("جاري تشغيل الأداة وجلب المباريات...")

    try:
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        target_leagues = [
            "Saudi", "Saudi Professional", "King", "Cup", 
            "AFC", "Champions League", "Europa", 
            "Premier League", "La Liga", "Serie A", 
            "Ligue 1", "Brasileiro", "Gulf", "الدوري السعودي", "كأس الملك", "Leagues Cup"
        ]
        
        clean_matches = []
        for match in dataset_items:
            league = match.get("competition", "") or match.get("competitionName", "") or match.get("league", "")
            
            if any(target.lower() in league.lower() for target in target_leagues):
                if "Friendly" in league or "ودية" in league:
                    continue
                
                # استخراج معرفات الفرق لبناء روابط الشعارات الرسمية مباشرة
                home_id = match.get("homeTeamId", "")
                away_id = match.get("awayTeamId", "")
                
                # روابط الشعارات الرسمية المباشرة بناءً على معرفات 365Scores
                home_logo = f"https://imagecache.365scores.com/image/upload/f_auto,w_160,h_160,c_limit,q_auto:eco/teams/{home_id}" if home_id else ""
                away_logo = f"https://imagecache.365scores.com/image/upload/f_auto,w_160,h_160,c_limit,q_auto:eco/teams/{away_id}" if away_id else ""
                
                # تخصيص اسم القناة بناءً على اسم البطولة
                channel_name = "beIN SPORTS"
                if "Saudi" in league or "الدوري السعودي" in league or "King" in league or "كأس" in league:
                    channel_name = "SSC Sports"
                elif "Champions League" in league:
                    channel_name = "beIN Sports HD 1"

                clean_matches.append({
                    "league_name": league,
                    "home_team": match.get("homeTeam", ""),
                    "away_team": match.get("awayTeam", ""),
                    "match_time": match.get("gameTime", "توقيت غير محدد"),
                    "home_team_logo": home_logo,
                    "away_team_logo": away_logo,
                    "status": match.get("statusText", "مجدولة"),
                    "channels": [{"name": channel_name, "commentator": "معلق المباراة"}]
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
        print(f"🔥 تم تحديث {len(matches_list)} مباراة مع الشعارات والقنوات الرسمية بنجاح في الفايربيس!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_365scores_matches()
    update_firebase(data)
