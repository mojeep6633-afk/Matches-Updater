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

    # 3. تحليل الصفحة واستخراج بيانات الأندية والبطولات بأمان تام
    championships = soup.find_all('div', class_='matchCard')
    
    for champ in championships:
        try:
            league_title = champ.find('div', class_='title')
            league_name = league_title.find('h2').text.strip() if league_title and league_title.find('h2') else "بطولة غير معروفة"
            
            matches_list = champ.find_all('div', class_='item')
            
            for match in matches_list:
                try:
                    teams = match.find_all('div', class_='team')
                    if len(teams) < 2:
                        continue # تخطي المباريات التي لا تحتوي على طرفين مكتملين
                        
                    home_tag = teams[0].find('p')
                    away_tag = teams[1].find('p')
                    
                    if not home_tag or not away_tag:
                        continue

                    home_team = home_tag.text.strip()
                    away_team = away_tag.text.strip()
                    
                    home_img = teams[0].find('img')
                    away_img = teams[1].find('img')
                    home_logo = home_img['src'] if home_img and 'src' in home_img else ""
                    away_logo = away_img['src'] if away_img and 'src' in away_img else ""
                    
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
                except Exception as match_err:
                    print(f"تخطي مباراة بسبب خطأ جزئي: {match_err}")
                    continue
        except Exception as champ_err:
            print(f"تخطي بطولة بسبب خطأ في القراءة: {champ_err}")
            continue

    print(f"تم العثور على {len(matches_data)} مباراة سارية.")

    # 4. تحديث فايربيس (مسح القديم وإضافة الجديد)
    if matches_data:
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        print("تم مسح بيانات الأمس القديمة.")

        for match_id, match_info in matches_data:
            collection_ref.document(str(match_id)).set(match_info)
            
        print("تم تحديث المباريات في فايربيس بنجاح! 🚀")
    else:
        print("لم يتم العثور على مباريات صالحة لتحديثها اليوم.")

if __name__ == "__main__":
    main()
