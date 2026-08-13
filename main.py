import requests

# الرابط الرئيسي لواجهة برمجة تطبيقات كرة القدم
url = "https://api-sports.io"

# أدخل مفتاح الـ API الخاص بك هنا (تلقاه في لوحة تحكم حسابك)
API_KEY = "ضع_مفتاح_الـ_API_الخاص_بك_هنا"

# تحديد المعاملات: الدوري السعودي، الموسم الحالي، واللغة العربية
# ملاحظة: يمكنك تغيير السنة (season) حسب الموسم المطلوب
headers = {
    'x-apisports-key': API_KEY
}

params = {
    'league': '307',       # معرف الدوري السعودي للمحترفين
    'season': '2025',      # حدد سنة الموسم الحالي المتاح بالمنصة
    'lang': 'ar'           # جلب الأسماء باللغة العربية
}

try:
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    # التحقق من نجاح الطلب ووجود بيانات
    if response.status_code == 200 and data.get("response"):
        # استخراج قائمة الترتيب
        standings = data["response"][0]["league"]["standings"][0]
        
        print(f"=== ترتيب الدوري السعودي للمحترفين ===")
        print(f"{'المركز':<6} | {'الفريق':<20} | {'النقاط':<6} | {'لعب':<5} | {'فوز':<5} | {'تعادل':<5} | {'خسارة':<5}")
        print("-" * 70)
        
        for team in standings:
            rank = team["rank"]
            team_name = team["team"]["name"]  # سيظهر بالعربية بفضل معامل lang=ar
            points = team["points"]
            played = team["all"]["played"]
            win = team["all"]["win"]
            draw = team["all"]["draw"]
            lose = team["all"]["lose"]
            
            print(f"{rank:<6} | {team_name:<20} | {points:<6} | {played:<5} | {win:<5} | {draw:<5} | {lose:<5}")
            
    else:
        print("خطأ في جلب البيانات أو أن الموسم لم يبدأ بعد.")
        if "errors" in data and data["errors"]:
            print("تفاصيل الخطأ:", data["errors"])

except Exception as e:
    print(f"حدث خطأ أثناء الاتصال بالـ API: {e}")
