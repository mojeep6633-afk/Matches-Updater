import json
import os
from datetime import datetime
import requests
import firebase_admin
from firebase_admin import credentials, firestore

def get_api_football_matches():
    API_KEY = "12d594efcd4cf9df22a2dba5067a8254"
    date_today = datetime.now().strftime("%Y-%m-%d")
    
    fixtures_url = "https://v3.football.api-sports.io/fixtures"
    querystring = {"date": date_today, "timezone": "Asia/Riyadh"}
    headers = {"x-apisports-key": API_KEY}

    print(f"جاري سحب مباريات اليوم ({date_today}) من API-Football...")

    try:
        response = requests.get(fixtures_url, headers=headers, params=querystring)
        if response.status_code != 200:
            print(f"خطأ في الاتصال: {response.status_code}")
            return []
            
        data = response.json()
        fixtures = data.get("response", [])
        
        # الكلمات الدلالية المبسطة لضمان التقاط جميع البطولات
        target_keywords = [
            "saudi", "king cup", "gulf", "afc", 
            "champions league", "europa league", 
            "premier league", "la liga", "primera", 
            "serie a", "ligue 1", "brasileiro"
        ]
        
        clean_matches = []
        
        for item in fixtures:
            league = item.get("league", {})
            # دمج اسم الدولة واسم البطولة لضمان البحث الصحيح
            league_name = f"{league.get('country', '')} {league.get('name', '')}".strip()
            
            if any(keyword.lower() in league_name.lower() for keyword in target_keywords):
                
                fixture = item.get("fixture", {})
                fixture_id = fixture.get("id")
                teams = item.get("teams", {})
                
                date_iso = fixture.get("date", "")
                match_time = "توقيت غير محدد"
                if date_iso:
                    dt_obj = datetime.fromisoformat(date_iso.replace("Z", "+00:00"))
                    match_time = dt_obj.strftime("%H:%M")

                channel_name = "غير متوفر"
                if fixture_id:
                    tv_url = "https://v3.football.api-sports.io/fixtures/tv"
                    tv_qs = {"fixture": fixture_id}
                    try:
                        tv_res = requests.get(tv_url, headers=headers, params=tv_qs)
                        if tv_res.status_code == 200:
                            tv_data = tv_res.json().get("response", [])
                            if tv_data:
                                channels = [ch.get("tv", {}).get("name") for ch in tv_data if ch.get("tv", {}).get("name")]
                                if channels:
                                    channel_name = " | ".join(channels)
                    except:
                        pass
                
                clean_matches.append({
                    "league_name": league.get("name", "غير معروف"), 
                    "home_team": teams.get("home", {}).get("name", "غير معروف"),
                    "away_team": teams.get("away", {}).get("name", "غير معروف"),
                    "match_time": match_time,
                    "home_team_logo": teams.get("home", {}).get("logo", ""),  
                    "away_team_logo": teams.get("away", {}).get("logo", ""),  
                    "status": fixture.get("status", {}).get("long", "مجدولة"),
                    "channels": [{"name": channel_name, "commentator": "غير محدد"}]
                })
                
        return clean_matches
        
    except Exception as e:
        print(f"حدث خطأ أثناء استخراج البيانات: {e}")
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
        doc_ref = db.collection("koora").document("daily_matches")
        doc_ref.set({"matches": matches_list, "last_updated": datetime.now().isoformat()})
        print(f"✅ تم تحديث {len(matches_list)} مباراة بنجاح عبر API-Football!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_api_football_matches()
    update_firebase(data)
