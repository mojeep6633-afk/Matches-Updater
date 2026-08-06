import os
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    print("بدأ تشغيل الخيار الثالث (سيرفر في الجول المفتوح)...")

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

    # 2. جلب المباريات بدون أي مفاتيح تسجيل
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"جاري جلب مباريات ليوم {today}...")
    
    url = f"https://api.filgoal.com/api/matches/getMatchesByDate?date={today}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"فشل جلب البيانات، رمز الاستجابة: {response.status_code}")
            return
            
        matches_list = response.json()
    except Exception as e:
        print(f"فشل الاتصال: {e}")
        return

    matches_data = []

    # 3. ترتيب البيانات لإرسالها
    if isinstance(matches_list, list):
        for match in matches_list:
            try:
                home_team = match.get('HomeTeamName', 'غير معروف')
                away_team = match.get('AwayTeamName', 'غير معروف')
                league_name = match.get('ChampionshipName', 'غير محدد')
                
                # استخراج الوقت بصيغة 24 ساعة (مثال: 19:30)
                match_date_str = match.get('Date', '') 
                time_only = match_date_str.split('T')[1][:5] if 'T' in match_date_str else "00:00"
                
                match_id = f"{home_team}_{away_team}".replace(" ", "_")

                match_info = {
                    "homeTeam": home_team,
                    "homeTeamLogo": "",
                    "awayTeam": away_team,
                    "awayTeamLogo": "",
                    "time": time_only,
                    "league": league_name,
                    "channelName": match.get('ChannelName', 'beIN Sports'),
                    "channelLogo": "",
                    "channelId": abs(hash(match_id)) % (10 ** 8),
                    "timestamp": firestore.SERVER_TIMESTAMP
                }
                matches_data.append((match_id, match_info))
            except Exception as match_err:
                continue

    print(f"تم العثور على {len(matches_data)} مباراة حقيقية.")

    # 4. إرسال المباريات إلى فايربيس لإنشاء المجموعة فوراً
    if matches_data:
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        print("تم مسح البيانات القديمة.")

        for match_id, match_info in matches_data:
            collection_ref.document(str(match_id)).set(match_info)
            
        print("تم إرسال المباريات بنجاح، ستجد مجموعة daily_matches الآن في فايربيس! 🚀")
    else:
        print("لم يتم العثور على مباريات اليوم.")

if __name__ == "__main__":
    main()
