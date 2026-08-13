import json
import os
from datetime import datetime
import requests
import firebase_admin
from firebase_admin import credentials, firestore

def fetch_direct_matches():
    # الرابط المباشر بعد إضافة sportId=1 الخاصة بكرة القدم
    url = "https://webws.365scores.com/web/games/current/?appTypeId=5&sportId=1&langId=27&timezoneName=Asia/Riyadh"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    print("جاري سحب المباريات من المصدر الرسمي لـ 365Scores مباشرة...")

    try:
        response = requests.get(url, headers=headers)
        data = response.json()

        competitions_dict = {c['id']: c['name'] for c in data.get('competitions', [])}
        competitors_dict = {c['id']: c['name'] for c in data.get('competitors', [])}
        tv_networks_dict = {tv['id']: tv['name'] for tv in data.get('tvNetworks', [])}

        # الفلتر باللغة العربية بناءً على ما يرسله السيرفر
        target_keywords = [
            "دوري", "كأس", "بطولة", "ودي", 
            "آسيا", "أوروبا", "إنجليزي", "إسباني", "إيطالي", 
            "فرنسي", "سعودي", "خليجي", "Leagues Cup"
        ]

        clean_matches = []
        
        for game in data.get('games', []):
            comp_name = competitions_dict.get(game.get('competitionId', -1), "بطولة غير معروفة")
            
            # فلترة البطولات
            if any(keyword.lower() in comp_name.lower() for keyword in target_keywords):
                
                home_id = game.get('homeCompetitorId', -1)
                away_id = game.get('awayCompetitorId', -1)

                # روابط الشعارات بصيغة PNG الصريحة
                home_logo = f"https://imagecache.365scores.com/image/upload/f_png,w_150/Teams/{home_id}.png" if home_id != -1 else ""
                away_logo = f"https://imagecache.365scores.com/image/upload/f_png,w_150/Teams/{away_id}.png" if away_id != -1 else ""

                # استخراج أسماء القنوات الحقيقية
                channel_names = []
                for tv in game.get('tvNetworks', []):
                    if isinstance(tv, dict):
                        channel_names.append(tv.get('name', ''))
                    else:
                        channel_names.append(tv_networks_dict.get(tv, ''))
                
                final_channel = " | ".join(filter(None, channel_names)) if channel_names else "غير متوفر"

                clean_matches.append({
                    "league_name": comp_name,
                    "home_team": competitors_dict.get(home_id, "غير معروف"),
                    "away_team": competitors_dict.get(away_id, "غير معروف"),
                    "match_time": game.get('startTime', "توقيت غير محدد"),
                    "home_team_logo": home_logo,
                    "away_team_logo": away_logo,
                    "status": "مجدولة",
                    "channels": [{"name": final_channel, "commentator": "غير محدد"}]
                })
        
        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء الاتصال بالمصدر: {e}")
        return []

def update_firebase(matches_list):
    if not matches_list:
        print("لا توجد مباريات مطابقة اليوم في المصدر.")
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
        print(f"✅ تم تحديث {len(matches_list)} مباراة بنجاح (مع قنوات حقيقية وشعارات PNG)!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = fetch_direct_matches()
    update_firebase(data)
