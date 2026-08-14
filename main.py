import requests
from datetime import datetime
import pytz
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json
import sys

# 1. حل مشكلة طباعة اللغة العربية في سيرفرات GitHub
sys.stdout.reconfigure(encoding='utf-8')

# ==========================================
# 2. إعداد فايربيس وقراءة الأسرار
# ==========================================
try:
    # جلب مفتاح فايربيس من GitHub Secrets (بالاسم الموجود في صورتك)
    firebase_key_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    
    if firebase_key_json:
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("firebase_key.json")
        
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("تم الاتصال بفايربيس بنجاح! 🎉")
except Exception as e:
    print(f"تحذير: لم يتم الاتصال بفايربيس: {e}")

# جلب المفتاح الخاص بـ API من الأسرار
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("خطأ: لم يتم العثور على API_KEY. تأكد من إضافته في الأسرار.")
    sys.exit(1)

# ==========================================
# 3. إعداد التوقيت والتاريخ (السعودية)
# ==========================================
saudi_tz = pytz.timezone('Asia/Riyadh')
today_date = datetime.now(saudi_tz).strftime('%Y-%m-%d')

# إعداد طلب API-Football
url_fixtures = "https://v3.football.api-sports.io/fixtures"
querystring = {
    "league": "307",  # معرف الدوري السعودي
    "season": "2026", # الموسم الحالي
    "date": today_date,
    "timezone": "Asia/Riyadh" # إرجاع الوقت بتوقيت السعودية مباشرة
}

headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": API_KEY
}

# ==========================================
# 4. جلب المباريات والرفع لفايربيس
# ==========================================
try:
    print(f"جاري البحث عن مباريات ليوم: {today_date}")
    response = requests.get(url_fixtures, headers=headers, params=querystring)
    data = response.json()
    
    matches_today = data.get("response", [])
    
    if len(matches_today) == 0:
        print("لا يوجد مباريات اليوم في الدوري السعودي.")
    
    for match in matches_today:
        fixture_id = str(match["fixture"]["id"])
        
        # أسماء الفرق والشعارات
        home_team = match["teams"]["home"]["name"]
        away_team = match["teams"]["away"]["name"]
        home_logo = match["teams"]["home"]["logo"]
        away_logo = match["teams"]["away"]["logo"]
        
        # استخراج الوقت وتنسيقه (مثال: 09:00 م)
        match_datetime_iso = match["fixture"]["date"]
        dt = datetime.fromisoformat(match_datetime_iso)
        time_str = dt.strftime("%I:%M %p")
        time_arabic = time_str.replace("AM", "ص").replace("PM", "م")
        
        # جلب القناة الناقلة (مع وضع ثمانية الرياضية كقناة افتراضية)
        url_tv = "https://v3.football.api-sports.io/fixtures/tv"
        tv_querystring = {"fixture": fixture_id}
        tv_response = requests.get(url_tv, headers=headers, params=tv_querystring).json()
        tv_data = tv_response.get("response", [])
        
        channel_name = "ثمانية الرياضية" # الناقل الرسمي الحالي
        if tv_data:
            channels_list = [tv["tv"]["name"] for tv in tv_data]
            raw_channel = " , ".join(channels_list)
            # فلترة ذكية: إذا أرجع הـ API قنوات قديمة (SSC)، نتمسك بـ "ثمانية"
            if "SSC" not in raw_channel.upper():
                channel_name = raw_channel

        print(f"المباراة: {home_team} ضد {away_team} | الوقت: {time_arabic} | القناة: {channel_name}")

        # تجهيز البيانات للرفع
        match_data = {
            "home_team": home_team,
            "away_team": away_team,
            "home_logo": home_logo,
            "away_logo": away_logo,
            "match_time": time_arabic,
            "match_date": today_date,
            "channel": channel_name
        }
        
        # الرفع إلى فايربيس
        if 'db' in locals():
            db.collection('matches').document(fixture_id).set(match_data, merge=True)
            print("تم الرفع لفايربيس بنجاح!")
            
        print("-" * 40)

except Exception as e:
    print(f"حدث خطأ أثناء تشغيل السكربت: {e}")
