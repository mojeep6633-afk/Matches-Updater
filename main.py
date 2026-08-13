
Logo
News


UP TO 30% OFF
For any subscription according to the chosen duration

HOW TO GET STARTED WITH API-NFL: THE COMPLETE BEGINNER’S GUIDE
August 7, 2026
Getting started with API-NFL is straightforward, e ...

Read More
HOW TO OPTIMIZE API-SPORTS CALLS AND QUOTA USAGE
July 27, 2026
An efficient API-SPORTS integration is not just ab ...

Read More
FIFA World Cup 2026: Group Stage Recap and Complete Match Reports With API-Football
July 1, 2026
The FIFA World Cup 2026 group stage is now complet ...

Read More
FIVB U17 Volleyball World Championships 2026: Guide to Using Data With API-SPORTS
June 26, 2026
In August 2026, the FIVB will stage two major glob ...

Read More
FIFA World Cup 2026 Lineups: All Teams, Coaches and Players
June 4, 2026
The 2026 World Cup will be the biggest in history. ...

Read More
Home
Dashboard
APIs

API-FOOTBALL
30% Used

API-AFL
0% Used

API-BASEBALL
0% Used

API-BASKETBALL
0% Used

API-FORMULA-1
0% Used

API-HANDBALL
0% Used

API-HOCKEY
0% Used

API-MMA
0% Used

API-NBA
0% Used

API-NFL
0% Used

API-RUGBY
0% Used

API-VOLLEYBALL
0% Used
Requests
My Activity
10:35
v3/fixtures/tv?fixture=1607182 #Football
10:35
v3/fixtures/tv?fixture=1602972 #Football
10:35
v3/fixtures/tv?fixture=1581501 #Football
10:35
v3/fixtures/tv?fixture=1546425 #Football
10:35
v3/fixtures/tv?fixture=1526952 #Football
10:35
v3/fixtures/tv?fixture=1511648 #Football
10:35
v3/fixtures/tv?fixture=1511641 #Football
10:35
v3/fixtures/tv?fixture=1526951 #Football
10:35
v3/fixtures/tv?fixture=1511646 #Football
10:35
v3/fixtures?date=2026-08-13&timezone=Asia/Riyadh #Football
10:34
v3/fixtures/tv?fixture=1607182 #Football
10:34
v3/fixtures/tv?fixture=1602972 #Football
10:34
v3/fixtures/tv?fixture=1581501 #Football
10:34
v3/fixtures/tv?fixture=1546425 #Football
10:34
v3/fixtures/tv?fixture=1526952 #Football
2026© Api-Sports
Quick Actions


User Profile
ابو فراس العبيدي
mojeep6633@gmail.com
My Profile
Account settings and more
My Access
Api-Key and active subscriptions
My Team
Manage members access
My Transactions
Transactions and invoices
My Scripts
File generation
Quota Alerts
Track your Apis consumption


Recent Notifications 0
0 Notifications
Avatar
AI Bot
Online
اريد كود الدوري السعودي
كود الدوري السعودي (Pro League) هو 307.

هذا هو الرمز الذي تحتاجه لاستخدام الدوري السعودي في الـ API. إذا كنت تبحث عن منافسات سعودية أخرى، لدينا أيضاً:

Crown Prince Cup (827)
King's Cup (504)
Super Cup (826)
Division 1 (308)
Division 2 (309)
هل تحتاج إلى مساعدة إضافية؟ 😊

import requests url = "https://v3.football.api-sports.io/fixtures" API_KEY = "12d594efcd4cf9df22a2dba5067a8254" headers = { 'x-apisports-key': API_KEY } # المعاملات المطلوبة لجلب جدول مباريات الموسم كاملاً params = { 'league': '307', # معرف الدوري السعودي للمحترفين 'season': '2026', # تحديد موسم 2026-2027 الحالي 'lang': 'ar' # عرض أسماء الأندية والملاعب بالعربية } try: response = requests.get(url, headers=headers, params=params) data = response.json() if response.status_code == 200 and data.get("response"): fixtures_list = data["response"] print(f"=== جدول مباريات الدوري السعودي للمحترفين ===") print(f"{'التاريخ':<12} | {'الجولة':<10} | {'صاحب الأرض':<20} | {'الضيف':<20} | {'الملعب':<25}") print("-" * 95) # استخراج أول 15 مباراة كمثال (يمكنك تصفح القائمة كاملة) for match in fixtures_list[:15]: # استخراج التاريخ فقط بدون الوقت اللحظي date = match["fixture"]["date"].split("T")[0] round_name = match["league"]["round"] home_team = match["teams"]["home"]["name"] away_team = match["teams"]["away"]["name"] venue = match["fixture"]["venue"]["name"] or "غير محدد" print(f"{date:<12} | {round_name:<10} | {home_team:<20} | {away_team:<20} | {venue:<25}") else: print("فشل جلب البيانات. تأكد من صحة مفتاح الـ API الخاص بك.") except Exception as e: print(f"حدث خطأ أثناء الاتصال: {e}")
كود جميل! 👍 لكن لاحظت بعض النقاط التي قد تحتاج إلى تعديل:

ملاحظات مهمة:
موسم 2026 قد لا يكون متاحاً بعد - جرب موسم 2024 أو 2025 الحالي
معامل lang قد لا يعمل - الـ API قد لا يدعمه، الأسماء ستكون بالإنجليزية
معامل status - يمكنك إضافته لتصفية المباريات (مثل status=NS للمباريات القادمة)
كود محسّن:
import requests

url = "https://v3.football.api-sports.io/fixtures"
API_KEY = "12d594efcd4cf9df22a2dba5067a8254"

headers = {
    'x-apisports-key': API_KEY
}

params = {
    'league': '307',      # الدوري السعودي
    'season': '2024',     # موسم متاح
    'status': 'NS'        # NS = Not Started (المباريات القادمة)
}

try:
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if response.status_code == 200 and data.get("response"):
        fixtures_list = data["response"]

        print(f"=== جدول مباريات الدوري السعودي للمحترفين ===\n")
        print(f"{'التاريخ':<12} | {'الجولة':<15} | {'صاحب الأرض':<20} | {'الضيف':<20}")
        print("-" * 75)

        for match in fixtures_list[:15]:
            date = match["fixture"]["date"].split("T")[0]
            round_name = match["league"]["round"]
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]

            print(f"{date:<12} | {round_name:<15} | {home_team:<20} | {away_team:<20}")
    else:
        print("فشل جلب البيانات. تأكد من صحة البيانات.")

except Exception as e:
    print(f"خطأ: {e}")
