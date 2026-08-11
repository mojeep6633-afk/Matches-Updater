import json
import os
import requests
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime

# مفتاح الـ API الخاص بك
API_KEY = "12d594efcd4cf9df22a2dba5067a8254" 
BASE_URL = "https://v3.football.api-sports.io"

def get_todays_matches():
    headers = {
        "x-rapidapi-host": "v3.football.api-sports.io",
        "x-rapidapi-key": API_KEY
    }
    
    # جلب مباريات اليوم
    today = datetime.now().strftime("%Y-%m-%d")
    
    # أضفنا توقيت السعودية عشان الأوقات تجي جاهزة ومضبوطة للتطبيق
    params = {
        "date": today,
        "timezone": "Asia/Riyadh" 
    }
    
    try:
        response = requests.get(f"{BASE_URL}/fixtures", headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        
        matches_list = []
        
        # حالياً سنسحب كل المباريات للتأكد من وصولها للفايربيس
        for fixture in data.get("response", []):
            league = fixture.get("league", {}).get("name", "بطولة غير معروفة")
            home_team = fixture.get("teams", {}).get("home", {}).get("name", "فريق 1")
            away_team = fixture.get("teams", {}).get("away", {}).get("name", "فريق 2")
            home_logo = fixture.get("teams", {}).get("home", {}).get("logo", "")
            away_logo = fixture.get("teams", {}).get("away", {}).get("logo", "")
            
            # الوقت يأتي بصيغة جاهزة (ISO 8601) من الـ API
            match_time = fixture.get("fixture", {}).get("date", "")
            
            # هيكلة البيانات كما يتوقعها تطبيق الأندرويد تماماً
            matches_list.append({
                "league_name": league,
                "home_team": home_team,
                "away_team": away_team,
                "match_time": match_time,
                "home_team_logo": home_logo,
                "away_team_logo": away_logo,
                "channels": [
                    {
                        "name": "غير محدد", # الـ API لا يوفر القنوات، سنتركها كقيمة افتراضية
                        "commentator": "" 
                    }
                ]
            })
            
        return matches_list
    except Exception as e:
        print(f"خطأ في API-Football: {e}")
        return []

def update_firebase(matches_list):
    if not matches_list:
        print("لا توجد مباريات اليوم نهائياً.")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_cert_string:
        print("خطأ: لم يتم العثور على مفتاح فايربيس السري في إعدادات جيت هاب")
        return

    firebase_cert = json.loads(firebase_cert_string)
    cred = credentials.Certificate(firebase_cert)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    
    # 🔴 وضع البيانات في حقل matches كما يتوقع تطبيق الأندرويد
    doc_ref = db.collection("koora").document("daily_matches")
    doc_ref.set({"matches": matches_list})

    print(f"تم تحديث فايربيس بنجاح بـ {len(matches_list)} مباراة!")

if __name__ == "__main__":
    print("بدأ سحب وتجهيز جدول المباريات من API-Football...")
    todays_matches = get_todays_matches()
    update_firebase(todays_matches)
