import requests

url = "https://v3.football.api-sports.io/fixtures"
API_KEY = "12d594efcd4cf9df22a2dba5067a8254"

headers = {
    'x-apisports-key': API_KEY
}

# المعاملات المطلوبة لجلب جدول مباريات الموسم كاملاً
params = {
    'league': '307',       # معرف الدوري السعودي للمحترفين
    'season': '2026',      # تحديد موسم 2026-2027 الحالي
    'lang': 'ar'           # عرض أسماء الأندية والملاعب بالعربية
}

try:
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if response.status_code == 200 and data.get("response"):
        fixtures_list = data["response"]
        
        print(f"=== جدول مباريات الدوري السعودي للمحترفين ===")
        print(f"{'التاريخ':<12} | {'الجولة':<10} | {'صاحب الأرض':<20} | {'الضيف':<20} | {'الملعب':<25}")
        print("-" * 95)
        
        # استخراج أول 15 مباراة كمثال (يمكنك تصفح القائمة كاملة)
        for match in fixtures_list[:15]:
            # استخراج التاريخ فقط بدون الوقت اللحظي
            date = match["fixture"]["date"].split("T")[0]
            round_name = match["league"]["round"]
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            venue = match["fixture"]["venue"]["name"] or "غير محدد"
            
            print(f"{date:<12} | {round_name:<10} | {home_team:<20} | {away_team:<20} | {venue:<25}")
            
    else:
        print("فشل جلب البيانات. تأكد من صحة مفتاح الـ API الخاص بك.")

except Exception as e:
    print(f"حدث خطأ أثناء الاتصال: {e}")
