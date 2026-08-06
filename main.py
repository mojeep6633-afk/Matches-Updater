import os
import json
import requests
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore

def main():
    print("بدأ تشغيل سكربت جلب المباريات المطور (API)...")

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

    # 2. جلب مباريات اليوم باستخدام API رياضي مستقر
    today = datetime.now().strftime("%Y-%m-%d")
    print(f"جاري جلب مباريات ليوم {today}...")
    
    # سنستخدم هنا مصدر API مجاني وعالمي للمباريات (Football-Data أو ما يعادله)
    # ملاحظة: يمكنك وضع مفتاح مجاني من موقع football-data.org لاحقاً إن أردت، أو استخدام رابط عام
    url = f"https://api.football-data.org/v4/matches?date={today}"
    
    # إذا كنت تستخدم مفتاح API خاص بك، ضع الهيدر التالي (اختياري حالياً):
    headers = {
        'X-Auth-Token': os.environ.get('FOOTBALL_DATA_API_KEY', '') 
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"فشل جلب البيانات، رمز الاستجابة: {response.status_code}")
            return
            
        data = response.json()
        matches_list = data.get('matches', [])
    except Exception as e:
        print(f"فشل الاتصال بالـ API: {e}")
        return

    matches_data = []

    for match in matches_list:
        try:
            home_team = match['homeTeam']['name']
            away_team = match['awayTeam']['name']
            league_name = match['competition']['name']
            
            # استخراج الوقت بصيغة سريعة
            utc_time = match['utcDate'] # مثال: 2026-08-06T19:00:00Z
            time_only = utc_time.split('T')[1][:5] if 'T' in utc_time else "غير محدد"
            
            match_id = f"{home_team}_{away_team}".replace(" ", "_")

            match_info = {
                "homeTeam": home_team,
                "homeTeamLogo": match['homeTeam'].get('crest', ''),
                "awayTeam": away_team,
                "awayTeamLogo": match['awayTeam'].get('crest', ''),
                "time": time_only,
                "league": league_name,
                "channelName": "beIN Sports", # قناة افتراضية أو يمكن تخصيصها
                "channelLogo": "",
                "channelId": abs(hash(match_id)) % (10 ** 8),
                "timestamp": firestore.SERVER_TIMESTAMP
            }
            matches_data.append((match_id, match_info))
        except Exception as match_err:
            print(f"تخطي مباراة بسبب خطأ في البيانات: {match_err}")
            continue

    print(f"تم العثور على {len(matches_data)} مباراة.")

    # 3. تحديث فايربيس (مسح القديم وإضافة الجديد)
    if matches_data:
        docs = collection_ref.stream()
        for doc in docs:
            doc.reference.delete()
        print("تم مسح البيانات القديمة.")

        for match_id, match_info in matches_data:
            collection_ref.document(str(match_id)).set(match_info)
            
        print("تم تحديث المباريات في فايربيس بنجاح وثبات تامة! 🚀")
    else:
        print("لم يتم العثور على مباريات اليوم عبر الـ API.")

if __name__ == "__main__":
    main()
