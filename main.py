import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    print("بدأ تشغيل سكربت جلب المباريات...")

    # 1. الاتصال بقاعدة بيانات فايربيس
    firebase_cert_string = os.environ.get('FIREBASE_SERVICE_ACCOUNT')
    if not firebase_cert_string:
        print("خطأ: لم يتم العثور على مفتاح فايربيس السري")
        return
        
    firebase_cert = json.loads(firebase_cert_string)
    cred = credentials.Certificate(firebase_cert)
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
        
    db = firestore.client()
    collection_ref = db.collection('daily_matches')

    # 2. الاتصال بالموقع الرياضي لسحب مباريات اليوم
    today = datetime.now().strftime("%m-%d-%Y")
    url = f"https://www.yallakora.com/match-center/?date={today}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    print(f"جاري قراءة المباريات ليوم {today}...")
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except Exception as e:
        print(f"فشل الاتصال بالموقع: {e}")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    matches_data = []

    # 3. تحليل الصفحة واستخراج بيانات الأندية والبطولات
    championships = soup.find_all('div', class_='matchCard')
    
    for champ in championships:
        league_title = champ.find('div', class_='title')
        league_name = league_title.find('h2').text.strip() if league_title else "بطولة غير معروفة"
        
        matches_list = champ.find_all('div', class_='item')
        
        for match in matches_list:
            try:
                teams = match.find_all('div', class_='team')
                home_team = teams[0].find('p').text.strip()
                away_team = teams[1].find('p').text.strip()
                
                home_logo = teams[0].find('img')['src'] if teams[0].find('img') else ""
                away_logo = teams[1].find('img')['src'] if teams[1].find('img') else ""
                
                match_time_div = match.find('span', class_='time')
                match_time = match_time_div.text.strip() if match_time_div else "غير محدد"
                
                channel_div = match.find('div', class_='channel')
                channel_name = channel_div.text.strip() if channel_div else "غير محددة"
                
                match_id = f"{home_team}_{away_team}".replace(" ", "_")

                match_info = {
                    "homeTeam": home_team,
                    "homeTeamLogo": home_logo,
                    "awayTeam": away_team,
                    "awayTeamLogo": away_logo,
                    "time": match_time,
                    "league": league_name,
                    "channelName": channel_name,
                    "channelLogo": "",
                    "channelId": abs(hash(match_id)) % (10 ** 8),
                    "timestamp": firestore.SERVER_TIMESTAMP
                }
                matches_data.append((match_id, match_info))
            except Exception as e:
                print(f"تم تخطي مباراة بسبب خطأ في القراءة: {e}")
                continue

    print(f"تم العثور على {len(matches_data)} مباراة.")

    # 4. تحديث فايربيس (مسح القديم وإضافة الجديد)
    if matches_data:
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        print("تم مسح بيانات الأمس.")

        for match_id, match_info in matches_data:
            collection_ref.document(str(match_id)).set(match_info)
            
        print("تم تحديث المباريات في فايربيس بنجاح! 🚀")
    else:
        print("لم يتم العثور على مباريات لتحديثها.")

if __name__ == "__main__":
    main()
