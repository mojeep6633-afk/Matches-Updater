import json
import os
from datetime import datetime
import firebase_admin
from apify_client import ApifyClient
from firebase_admin import credentials, firestore


def get_365scores_matches():
    # وضع مفتاح Apify مباشرة هنا لضمان عمله بدون أخطاء
    APIFY_TOKEN = "apify_api_yJ5YPMy0T1ecpOB21nFMhUzffI7HYL2P41nU"
    client = ApifyClient(APIFY_TOKEN)

    run_input = {
        "sport": "football",
        "category": "matches",
        "date": "today",
        "maxItems": 300,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "SA",
        },
    }

    print("جاري تشغيل كاشف 365Scores عبر Apify بالبروكسي العربي لجلب المباريات...")

    try:
        run = client.actor("apify/365scores-sports-data-scraper").call(
            run_input=run_input
        )
        dataset_items = client.dataset(run["defaultDatasetId"]).list().items

        clean_matches = []

        for match in dataset_items:
            league_name = match.get("competition", {}).get("name", "بطولة غير محددة")
            home_team = match.get("homeTeam", {}).get("name", "الفريق المضيف")
            home_logo = match.get("homeTeam", {}).get("logoUrl", "")
            away_team = match.get("awayTeam", {}).get("name", "الفريق الضيف")
            away_logo = match.get("awayTeam", {}).get("logoUrl", "")
            match_time = match.get("startTime", "")
            status = match.get("statusText", "لم تبدأ")

            broadcasters = match.get("broadcasters", [])
            channels_list = []

            if broadcasters:
                for b in broadcasters:
                    channels_list.append(
                        {
                            "name": b.get("name", "غير متوفر"),
                            "commentator": match.get("commentator", "غير محدد"),
                        }
                    )
            else:
                channels_list.append({"name": "غير معلن", "commentator": "غير محدد"})

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

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

    if not firebase_cert_string:
        print("خطأ: لم يتم العثور على مفتاح فايربيس السري في المتغيرات")
        return

    try:
        firebase_cert = json.loads(firebase_cert_string)
        cred = credentials.Certificate(firebase_cert)
    except Exception:
        cred = credentials.Certificate("serviceAccountKey.json")

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()

    doc_ref = db.collection("koora").document("daily_matches")
    doc_ref.set(
        {"matches": matches_list, "last_updated": datetime.now().isoformat()}
    )

    print(f"🔥 تم تحديث قاعدة بيانات فايربيس بنجاح بـ {len(matches_list)} مباراة!")


if __name__ == "__main__":
    todays_matches = get_365scores_matches()
    update_firebase(todays_matches)
