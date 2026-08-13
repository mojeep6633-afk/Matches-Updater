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

    print("جاري تشغيل الأداة وجلب عينة البيانات...")

    try:
        run = client.actor(actor_id).call(run_input=run_input)
        dataset_items = list(client.dataset(run["defaultDatasetId"]).iterate_items())
        
        if dataset_items:
            # طباعة أول مباراة بالكامل لنعرف أسماء حقول الشعارات والقنوات بدقة في السجلات
            print("--- عينة من هيكل بيانات المباراة الأولى ---")
            print(json.dumps(dataset_items[0], indent=2, ensure_ascii=False))
            print("------------------------------------------")
        
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
                
                # البحث الشامل عن أسماء القنوات
                tv_channel = match.get("tvChannel") or match.get("channel") or match.get("broadcasts") or match.get("channels") or match.get("tv") or "قنوات النقل الرسمية"
                if isinstance(tv_channel, list) and len(tv_channel) > 0:
                    if isinstance(tv_channel[0], dict):
                        tv_channel = tv_channel[0].get("name", "قنوات النقل الرسمية")
                    else:
                        tv_channel = str(tv_channel[0])
                elif isinstance(tv_channel, dict):
                    tv_channel = tv_channel.get("name", "قنوات النقل الرسمية")

                # البحث الشامل عن روابط الشعارات بكل الاحتمالات الممكنة
                home_logo = (
                    match.get("homeTeamImageUrl") or match.get("homeLogo") or 
                    match.get("homeTeamLogo") or match.get("homeTeamImage") or 
                    match.get("homeBadge") or match.get("homeImageUrl") or ""
                )
                away_logo = (
                    match.get("awayTeamImageUrl") or match.get("awayLogo") or 
                    match.get("awayTeamLogo") or match.get("awayTeamImage") or 
                    match.get("awayBadge") or match.get("awayImageUrl") or ""
                )
                
                clean_matches.append({
                    "league_name": league,
                    "home_team": match.get("homeTeam", "") or match.get("homeTeamName", "") or match.get("homeName", ""),
                    "away_team": match.get("awayTeam", "") or match.get("awayTeamName", "") or match.get("awayName", ""),
                    "match_time": match.get("gameTime", "") or match.get("time", "") or match.get("date", "توقيت غير محدد"),
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
        print(f"🔥 تم تحديث {len(matches_list)} مباراة بنجاح في الفايربيس!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_365scores_matches()
    update_firebase(data)
