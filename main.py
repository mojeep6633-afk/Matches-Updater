import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

def get_matches():
    print("جاري سحب المباريات للبطولات المطلوبة...")
    clean_matches = []
    
    # القوائم المطلوبة حرفياً
    target_leagues = [
        "دوري روشن السعودي", "الدوري السعودي للمحترفين", "كأس خادم الحرمين الشريفين", 
        "كأس الملك", "دوري أبطال آسيا", "دوري أبطال أوروبا", "الدوري الأوروبي", 
        "الدوري الإنجليزي", "الدوري الإسباني", "الدوري الإيطالي", "الدوري الفرنسي", 
        "الدوري البرازيلي", "الدوري الإسباني - ليغا", "الليغا"
    ]
    
    try:
        url = "https://www.yallakora.com/match-center/%D9%85%D8%A8%D8%A7%D8%B1%D8%A7%D8%A9-%D8%A7%D9%84%D9%8A%D9%88%D9%85?date="
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            match_cards = soup.find_all('div', {'class': 'matchCard'})
            
            for card in match_cards:
                try:
                    # استخراج اسم البطولة
                    league_elem = card.find_previous('div', {'class': 'title'})
                    league_name = league_elem.text.strip() if league_elem else ""
                    
                    # فلترة البطولات لتطابق طلبك حصرياً
                    if not any(t in league_name for t in target_leagues):
                        continue
                        
                    # استخراج أسماء الفريقين
                    home_elem = card.find('div', {'class': 'teamA'})
                    away_elem = card.find('div', {'class': 'teamB'})
                    home_team = home_elem.text.strip() if home_elem else "الفريق المضيف"
                    away_team = away_elem.text.strip() if away_elem else "الفريق الضيف"
                    
                    # التوقيت
                    time_elem = card.find('div', {'class': 'time'})
                    match_time = time_elem.text.strip() if time_elem else "غير محدد"
                    
                    # الشعارات
                    home_logo, away_logo = "", ""
                    imgs = card.find_all('img')
                    if len(imgs) >= 2:
                        home_logo = imgs[0].get('data-src') or imgs[0].get('src', '')
                        away_logo = imgs[1].get('data-src') or imgs[1].get('src', '')
                        
                    clean_matches.append({
                        "league_name": league_name,
                        "home_team": home_team,
                        "away_team": away_team,
                        "match_time": match_time,
                        "home_team_logo": home_logo,
                        "away_team_logo": away_logo,
                        "status": "مجدولة",
                        "channels": [{"name": "القنوات الناقلة الرسمية", "commentator": "غير محدد"}]
                    })
                except Exception:
                    continue
                    
        return clean_matches
    except Exception as e:
        print(f"خطأ أثناء سحب البيانات: {e}")
        return []

def update_firebase(matches_list):
    if not matches_list:
        print("مصفوفة المباريات فارغة، لا توجد مباريات مطابقة للبطولات المطلوبة اليوم.")
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
