import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

def get_matches():
    print("جاري سحب المباريات للبطولات المحددة...")
    clean_matches = []
    
    # القوائم أو الكلمات المفتاحية للبطولات المطلوبة باللغتين لتجنب أي نقص
    allowed_leagues = [
        "الدوري السعودي", "السعودي للمحترفين", "كأس الملك", "خادم الحرمين",
        "دوري أبطال آسيا", "أبطال آسيا", "دوري أبطال أوروبا", "الدوري الأوروبي",
        "الدوري الإنجليزي", "الدوري الإسباني", "الليغا", "الدوري الإيطالي",
        "الدوري الفرنسي", "الدوري البرازيلي", "الخليج"
    ]
    
    try:
        url = "https://www.yallakora.com/match-center/%D9%85%D8%A8%D8%A7%D8%B1%D8%A7%D8%A9-%D8%A7%D9%84%D9%8A%D9%88%D9%85?date="
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            tournaments = soup.find_all('div', {'class': 'tournaments-container'})
            
            if not tournaments:
                tournaments = soup.find_all('div', {'class': 'matchCard'})

            for t in soup.find_all('div', {'class': 'matchCard'}):
                try:
                    league_elem = t.find_previous('div', {'class': 'title'}) or t.find('div', {'class': 'title'})
                    league = league_elem.text.strip() if league_elem else "مباراة عامة"
                    
                    # التحقق مما إذا كانت البطولة من ضمن القائمة المطلوبة
                    is_target = any(alt in league for alt in allowed_leagues)
                    if not is_target:
                        continue
                        
                    home_elem = t.find('div', {'class': 'teamA'})
                    away_elem = t.find('div', {'class': 'teamB'})
                    time_elem = t.find('div', {'class': 'time'})
                    
                    home = home_elem.text.strip() if home_elem else "المضيف"
                    away = away_elem.text.strip() if away_elem else "الضيف"
                    match_time = time_elem.text.strip() if time_elem else "الوقت غير متوفر"
                    
                    # استخراج الشعارات إن وجدت
                    home_logo = ""
                    away_logo = ""
                    img_tags = t.find_all('img')
                    if len(img_tags) >= 2:
                        home_logo = img_tags[0].get('data-src') or img_tags[0].get('src', '')
                        away_logo = img_tags[1].get('data-src') or img_tags[1].get('src', '')

                    clean_matches.append({
                        "league_name": league,
                        "home_team": home,
                        "away_team": away,
                        "match_time": match_time,
                        "home_team_logo": home_logo,
                        "away_team_logo": away_logo,
                        "status": "مجدولة",
                        "channels": [{"name": "قنوات النقل الرسمية", "commentator": "غير محدد"}]
                    })
                except Exception:
                    continue
                    
        return clean_matches
    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return []

def update_firebase(matches_list):
    if not matches_list:
        print("مصفوفة المباريات فارغة، لم يتم العثور على مباريات مطابقة للبطولات المطلوبة اليوم.")
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
    matches = get_matches()
    update_firebase(matches)
