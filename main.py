import json
import os
from datetime import datetime
import firebase_admin
from apify_client import ApifyClient
from firebase_admin import credentials, firestore


def get_365scores_matches():
    # 1. ضع مفتاح الأمان (API Token) الخاص بحسابك في Apify هنا
    APIFY_TOKEN = os.environ.get("APIFY_TOKEN", "ضع_مفتاح_الأمان_الخاص_بك_هنا")
    client = ApifyClient(APIFY_TOKEN)

    # 2. إعداد المدخلات مع تفعيل البروكسي السكني السعودي لجلب القنوات والمعلقين العرب
    run_input = {
        "sport": "football",
        "category": "matches",
        "date": "today",
        "maxItems": 50,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "SA",  # تضمن سحب قنوات SSC و beIN والمعلقين العرب
        },
    }

    print(
        "جاري تشغيل كاشف 365Scores عبر Apify بالبروكسي العربي لجلب المباريات..."
    )

    try:
        # 3. تشغيل أداة الكشط في Apify واستقبال البيانات
        run = client.actor("apify/365scores-sports-data-scraper").call(
            run_input=run_input
        )
        dataset_items = client.dataset(run["defaultDatasetId"]).list().items

        clean_matches = []

        # 4. معالجة وتجهيز البيانات المستخرجة متوافقة مع تطبيقك
        for match in dataset_items:
            # اسم الدوري/المنافسة
            league_name = match.get("competition", {}).get(
                "name", "بطولة غير محددة"
            )

            # بيانات الفريق المضيف والشعار
            home_team = match.get("homeTeam", {}).get("name", "الفريق المضيف")
            home_logo = match.get("homeTeam", {}).get("logoUrl", "")

            # بيانات الفريق الضيف والشعار
            away_team = match.get("awayTeam", {}).get("name", "الفريق الضيف")
            away_logo = match.get("awayTeam", {}).get("logoUrl", "")

            # توقيت المباراة وحالتها من 365Scores
            match_time = match.get("startTime", "")  # صيغة ISO القياسية وعادة ما تكون بتوقيت مكة
            status = match.get("statusText", "لم تبدأ")

            # جلب القنوات والمعلقين المكتشفين بواسطة البروكسي
            broadcasters = match.get("broadcasters", [])
            channels_list = []

            if broadcasters:
                for b in broadcasters:
                    channels_list.append(
                        {
                            "name": b.get("name", "غير متوفر"),
                            "commentator": match.get(
                                "commentator", "غير محدد"
                            ),
                        }
                    )
            else:
                channels_list.append(
                    {"name": "غير معلن", "commentator": "غير محدد"}
                )

            # بناء الكائن النهائي لكل مباراة
            clean_matches.append(
                {
                    "league_name": league_name,
                    "home_team": home_team,
                    "away_team": away_team,
                    "match_time": match_time,
                    "status": status,
                    "home_team_logo": home_logo,
                    "away_team_logo": away_logo,
                    "channels": channels_list,
                }
            )

        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء سحب البيانات من Apify: {e}")
        return None


def update_firebase(matches_list):
    if not matches_list:
        print("مصفوفة المباريات فارغة، لن يتم تحديث فايربيس.")
        return

    # جلب اعتماد الحساب السري لـ Firebase من متغيرات البيئة (أو ضع المسار المباشر لملف الـ json)
    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_cert_string:
        print(
            "خطأ: لم يتم العثور على مفتاح فايربيس السري في المتغيرات (FIREBASE_SERVICE_ACCOUNT)"
        )
        return

    try:
        firebase_cert = json.loads(firebase_cert_string)
        cred = credentials.Certificate(firebase_cert)
    except Exception:
        # في حال كنت تختبر محلياً وتضع مسار الملف المباشر "serviceAccountKey.json" بدلاً من النص
        cred = credentials.Certificate("serviceAccountKey.json")

    # تهيئة اتصال فايربيس إذا لم يكن متصلاً مسبقاً
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    # رفع البيانات كاملة داخل مستند daily_matches في كوليكشن koora
    doc_ref = db.collection("koora").document("daily_matches")
    doc_ref.set(
        {"matches": matches_list, "last_updated": datetime.now().isoformat()}
    )

    print(
        f"🔥 تم تحديث قاعدة بيانات فايربيس بنجاح بـ {len(matches_list)} مباراة من 365Scores!"
    )


if __name__ == "__main__":
    # تشغيل السكربت بالكامل
    todays_matches = get_365scores_matches()
    update_firebase(todays_matches)
