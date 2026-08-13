import json
import os
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore


def get_matches():
    print("جاري سحب المباريات الرسمية فقط بدون الودية...")
    clean_matches = []
    
    try:
        url = "https://www.yallakora.com/match-center/%D9%85%D8%A8%D8%A7%D8%B1%D8%A7%D8%A9-%D8%A7%D9%84%D9%8A%D9%88%D9%85?date="
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            matches_box = soup.find_all('div', {'class': 'matchCard'})
            
            for m in matches_box:
                try:
                    league = m.find('div', {'class': 'title'}).text.strip()
                    
                    # شرط استبعاد المباريات الودية تماماً
                    if "ودية" in league or "friendly" in league.lower():
                        continue
                        
                    home = m.find('div', {'class': 'teamA'}).text.strip()
                    away = m.find('div', {'class': 'teamB'}).text.strip()
                    time = m.find('div', {'class': 'time'}).text.strip()
                    
                    clean_matches.append({
                        "league_name": league,
                        "home_team": home,
                        "away_team": away,
                        "match_time": time,
                        "status": "جاري التحديث",
                        "home_team_logo": "",
                        "away_team_logo": "",
                        "channels": [{"name": "قنوات SSC / beIN", "commentator": "غير محدد"}]
                    })
                except:
                    continue
                    
        return clean_matches if clean_matches else []

    except Exception as e:
        print(f"حدث خطأ أثناء سحب المباريات: {e}")
        return []


def update_firebase(matches_list):
    if not matches_list:
        print("مصفوفة المباريات فارغة، لن يتم تحديث فايربيس.")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_cert_string:
        print("خطأ: لم يتم العثور على مفتاح فايربيس السري")
        return

    try:
        firebase_cert = json.loads(firebase_cert_string)
        cred = credentials.Certificate(firebase_cert)
    except Exception:
        cred = credentials.Certificate("serviceAccountKey.json")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    doc_ref = db.collection("koora").document("daily_matches")
    doc_ref.set(
        {"matches": matches_list, "last_updated": datetime.now().isoformat()}
    )

    print(f"🔥 تم تحديث قاعدة بيانات فايربيس بنجاح بـ {len(matches_list)} مباراة رسمية فقط!")


if __name__ == "__main__":
    todays_matches = get_matches()
    update_firebase(todays_matches)
