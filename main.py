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

    run_input = {
        "mode": "liveScores",
        "sport": "football",
        "maxItems": 150
    }

    print("جاري تشغيل كاشف 365Scores وجلب البيانات المحدثة...")

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
            league = match.get("competition", "") or match.get("competitionName", "") or match.get("league", "") or match.get("competitionDisplayName", "")
            
            if any(target.lower() in league.lower() for target in target_leagues):
                if "Friendly" in league or "ودية" in league:
                    continue
                
                # استخراج اسم القناة الناقلة الحقيقية إن وجدت في البيانات
                tv_channel = match.get("tvChannel") or match.get("channel") or match.get("broadcasts") or match.get("tv") or "غير متوفر"
                if isinstance(tv_channel, list) and len(tv_channel) > 0:
                    tv_channel = tv_channel[0].get("name", "قنوات النقل الرسمية")
                elif not tv_channel or tv_channel == "غير متوفر":
                    tv_channel = "beIN Sports / SSC"

                # استخراج روابط الشعارات بدقة لضمان ظهورها
                home_logo = match.get("homeTeamImageUrl") or match.get("homeLogo") or match.get("homeTeamLogo") or match.get("homeTeamImage") or ""
                away_logo = match.get("awayTeamImageUrl") or match.get("awayLogo") or match.get("awayTeamLogo") or match.get("awayTeamImage") or ""
                
                clean_matches.append({
                    "league_name": league,
                    "home_team": match.get("homeTeam", "") or match.get("homeTeamName", ""),
                    "away_team": match.get("awayTeam", "") or match.get("awayTeamName", ""),
                    "match_time": match.get("gameTime", "") or match.get("time", "توقيت غير محدد"),
                    "home_team_logo": home_logo,
                    "away_team_logo": away_logo,
                    "status": match.get("statusText", "مجدولة"),
                    "channels": [{"name": str(tv_channel), "commentator": "غير محدد"}]
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
        print(f"🔥 تم تحديث {len(matches_list)} مباراة مع الشعارات والقنوات بنجاح في الفايربيس!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_365scores_matches()
    update_firebase(data)
