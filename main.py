import requests
import json

url = "https://v3.football.api-sports.io/fixtures"
API_KEY = "12d594efcd4cf9df22a2dba5067a8254"

headers = {
    'x-apisports-key': API_KEY
}

params = {
    'league': '307',       # الدوري السعودي للمحترفين
    'season': '2025',      # الموسم الحالي
    'status': 'NS'         # المباريات القادمة فقط
}

try:
    response = requests.get(url, headers=headers, params=params)

    # طباعة معلومات الاستجابة للتشخيص
    print(f"Status Code: {response.status_code}\n")

    data = response.json()

    # التحقق من وجود أخطاء في الاستجابة
    if data.get("errors") and len(data["errors"]) > 0:
        print(f"❌ خطأ من الـ API: {data['errors']}")

    # التحقق من عدد النتائج
    results_count = data.get("results", 0)
    print(f"📊 عدد المباريات المتاحة: {results_count}\n")

    if response.status_code == 200 and data.get("response") and len(data["response"]) > 0:
        fixtures_list = data["response"]

        print(f"=== جدول مباريات الدوري السعودي للمحترفين ===\n")
        print(f"{'التاريخ':<12} | {'الوقت':<8} | {'الجولة':<15} | {'صاحب الأرض':<20} | {'الضيف':<20}")
        print("-" * 95)

        for match in fixtures_list[:15]:
            try:
                date = match["fixture"]["date"].split("T")[0]
                time = match["fixture"]["date"].split("T")[1][:5]  # استخراج الوقت
                round_name = match["league"]["round"]
                home_team = match["teams"]["home"]["name"]
                away_team = match["teams"]["away"]["name"]

                print(f"{date:<12} | {time:<8} | {round_name:<15} | {home_team:<20} | {away_team:<20}")
            except KeyError as e:
                print(f"⚠️ خطأ في معالجة البيانات: {e}")
                continue
    else:
        print("❌ فشل جلب البيانات أو القائمة فارغة.")
        print(f"📋 الاستجابة الكاملة: {json.dumps(data, indent=2, ensure_ascii=False)}")

except requests.exceptions.ConnectionError:
    print("❌ خطأ في الاتصال بالإنترنت. تأكد من الاتصال.")
except requests.exceptions.Timeout:
    print("❌ انتهت مهلة الاتصال. حاول مرة أخرى.")
except Exception as e:
    print(f"❌ خطأ غير متوقع: {e}")
