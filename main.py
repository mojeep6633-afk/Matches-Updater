import json
import os
import time
from datetime import datetime, timedelta
import requests
import firebase_admin
from firebase_admin import credentials, firestore

def get_sofascore_matches():
    # جلب تاريخ اليوم
    date_today = datetime.now().strftime("%Y-%m-%d")
    url = f"https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date_today}"
    
    # ترويسات قوية لمحاكاة متصفح حقيقي وطلب البيانات باللغة العربية
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ar-SA,ar;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://www.sofascore.com",
        "Referer": "https://www.sofascore.com/"
    }

    print(f"جاري سحب مباريات اليوم ({date_today}) من SofaScore المباشر...")

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"فشل الاتصال بالسيرفر. رمز الخطأ: {response.status_code}")
            return []
            
        data = response.json()
        events = data.get("events", [])
        
        # الكلمات الدلالية للبطولات اللي طلبتها بالضبط
        target_keywords = [
            "سعودي", "محترفين", "ملك", "حرمين", "خليج", "تعاون", 
            "آسيا", "اسيا", "أوروب", "اوروب", "إنجليز", "انجليز", 
            "إسبان", "اسبان", "إيطال", "ايطال", "فرنس", "برازيل"
        ]
        
        clean_matches = []
        
        for event in events:
            tournament = event.get("tournament", {})
            tour_name = tournament.get("name", "")
            
            # إذا اسم البطولة يحتوي على أي من الكلمات المستهدفة
            if any(key in tour_name.lower() for key in target_keywords):
                
                event_id = event.get("id")
                home_team = event.get("homeTeam", {})
                away_team = event.get("awayTeam", {})
                
                home_id = home_team.get("id")
                away_id = away_team.get("id")
                
                # روابط صور PNG مباشرة من سيرفرات SofaScore
                home_logo = f"https://api.sofascore.app/api/v1/team/{home_id}/image" if home_id else ""
                away_logo = f"https://api.sofascore.app/api/v1/team/{away_id}/image" if away_id else ""
                
                # ضبط التوقيت ليكون بتوقيت السعودية (+3)
                match_timestamp = event.get("startTimestamp")
                if match_timestamp:
                    dt = datetime.utcfromtimestamp(match_timestamp) + timedelta(hours=3)
                    match_time = dt.strftime("%H:%M")
                else:
                    match_time = "توقيت غير محدد"
                    
                # استخراج القنوات الناقلة بطلب مخصص لكل مباراة
                channel_name = "غير متوفر"
                if event_id:
                    tv_url = f"https://api.sofascore.com/api/v1/event/{event_id}/tv-channels"
                    try:
                        tv_res = requests.get(tv_url, headers=headers)
                        if tv_res.status_code == 200:
                            tv_data = tv_res.json()
                            channels = []
                            for ch in tv_data.get("tvChannels", []):
                                ch_name = ch.get("title") or ch.get("tvNetwork", {}).get("name")
                                if ch_name:
                                    channels.append(ch_name)
                            if channels:
                                channel_name = " | ".join(channels)
                    except:
                        pass
                    
                    # إيقاف مؤقت بسيط لتجنب حظر السيرفر
                    time.sleep(0.1)
                
                clean_matches.append({
                    "league_name": tour_name,
                    "home_team": home_team.get("name", "غير معروف"),
                    "away_team": away_team.get("name", "غير معروف"),
                    "match_time": match_time,
                    "home_team_logo": home_logo,
                    "away_team_logo": away_logo,
                    "status": "مجدولة",
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
        print(f"✅ تم تحديث {len(matches_list)} مباراة بنجاح (سيرفر SofaScore)!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_sofascore_matches()
    update_firebase(data)
