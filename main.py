import requests
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore

# ==========================================
# 1. إعداد فايربيس (تأكد من وضع ملف json الخاص بصلاحيات فايربيس)
# ==========================================
# إذا كنت تستخدم GitHub Secrets، يمكنك تمرير محتوى الـ JSON كمتغير بيئة.
# افترض هنا أن ملف الصلاحيات اسمه firebase_key.json
try:
    cred = credentials.Certificate("firebase_key.json")
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("تم الاتصال بفايربيس بنجاح!")
except Exception as e:
    print(f"تحذير: لم يتم الاتصال بفايربيس: {e}")

# ==========================================
# 2. إعداد التوقيت والتاريخ (السعودية)
# ==========================================
saudi_tz = pytz.timezone('Asia/Riyadh')
today_date = datetime.now(saudi_tz).strftime('%Y-%m-%d')

# مفتاح الـ API (تذكر استخدام المفتاح الجديد)
API_KEY = "ضع_مفتاحك_الجديد_هنا"

# جلب مباريات اليوم (مع تحديد توقيت الرياض في الطلب)
url_fixtures = "https://v3.football.api-sports.io/fixtures"
querystring = {
    "league": "307", 
    "season": "2026", 
    "date": today_date,
    "timezone": "Asia/Riyadh"  # هذه الميزة تجعل الـ API يرجع الوقت بتوقيت السعودية مباشرة
}

headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY
}

try:
    print(f"جاري البحث عن مباريات ليوم: {today_date}")
    response = requests.get(url_fixtures, headers=headers, params=querystring)
    data = response.json()
    
    matches_today = data.get("response", [])
    
    if len(matches_today) == 0:
        print("لا يوجد مباريات اليوم في الدوري السعودي.")
    
    for match in matches_today:
        fixture_id = str(match["fixture"]["id"])
        
        # 1. أسماء الفرق والشعارات
        home_team = match["teams"]["home"]["name"]
        away_team = match["teams"]["away"]["name"]
        home_logo = match["teams"]["home"]["logo"]
        away_logo = match["teams"]["away"]["logo"]
        
        # 2. استخراج الوقت وتنسيقه (مثال: 09:00 م)
        # الـ API يرجع الوقت هكذا: 2026-08-14T21:00:00+03:00
        match_datetime_iso = match["fixture"]["date"]
        dt = datetime.fromisoformat(match_datetime_iso)
        
        # تحويل الوقت لـ (ساعات:دقائق ص/م)
        time_str = dt.strftime("%I:%M %p")
        time_arabic = time_str.replace("AM", "ص").replace("PM", "م")
        
        # 3. جلب القناة الناقلة (أو وضع ثمانية الرياضية افتراضياً)
        url_tv = "https://v3.football.api-sports.io/fixtures/tv"
        tv_querystring = {"fixture": fixture_id}
        tv_response = requests.get(url_tv, headers=headers, params=tv_querystring).json()
        tv_data = tv_response.get("response", [])
        
        channel_name = "ثمانية الرياضية" # القناة الافتراضية
        if tv_data:
            channels_list = [tv["tv"]["name"] for tv in tv_data]
            raw_channel = " , ".join(channels_list)
            # إذا جلب قنوات قديمة مثل SSC، نتجاهلها ونضع ثمانية
            if "SSC" not in raw_channel.upper():
                channel_name = raw_channel

        print(f"المباراة: {home_team} ضد {away_team} | الوقت: {time_arabic} | القناة: {channel_name}")

        # 4. رفع البيانات إلى فايربيس (Firestore كمثال)
        match_data = {
            "home_team": home_team,
            "away_team": away_team,
            "home_logo": home_logo,
            "away_logo": away_logo,
            "match_time": time_arabic,
            "match_date": today_date,
            "channel": channel_name
        }
        
        # استخدام merge=True حتى لا يحذف أي بيانات أخرى ربما أضفتها أنت يدوياً
        if 'db' in locals():
            db.collection('matches').document(fixture_id).set(match_data, merge=True)
            print("تم الرفع لفايربيس بنجاح!")
            
        print("-" * 40)

except Exception as e:
    print(f"حدث خطأ: {e}")
