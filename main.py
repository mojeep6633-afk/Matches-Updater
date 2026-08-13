import json
import os
from datetime import datetime
from apify_client import ApifyClient
import firebase_admin
from firebase_admin import credentials, firestore

def get_365scores_matches():
    # المفتاح المباشر الخاص بك
    APIFY_TOKEN = "apify_api_yJ5YPMy0T1ecpOB21nFMhUzffI7HYL2P41nU"
    client = ApifyClient(APIFY_TOKEN)

    run_input = {
        "sport": "football",
        "category": "matches",
        "date": "today",
        "maxItems": 100,
        "proxyConfiguration": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "SA",
        }
    }

    print("جاري تشغيل كاشف 365Scores عبر Apify بالبروكسي العربي لجلب المباريات...")

    try:
        run = client.actor("apify/365scores-sports-data-scraper").call(run_input=run_input)
        dataset_items = client.dataset(run["defaultDatasetId"]).list().items
        
        clean_matches = []
        for match in dataset_items:
            # فلترة المباريات الودية (استبعاد إذا وجد تصنيف Friendly)
            league = match.get("competition", {}).get("name", "")
            if "Friendly" in league or "ودية" in league:
                continue
                
            clean_matches.append(match)
            
        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء سحب البيانات من Apify: {e}")
        return None

def update_firebase(matches_list):
    if not matches_list:
        print("مصفوفة المباريات فارغة.")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    
    # محاولة تحميل شهادة الفايربيس
    try:
        if firebase_cert_string:
            firebase_cert = json.loads(firebase_cert_string)
            cred = credentials.Certificate(firebase_cert)
        else:
            cred = credentials.Certificate("serviceAccountKey.json")
            
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
            
        db = firestore.client()
        doc_ref = db.collection("koora").document("daily_matches")
        doc_ref.set({"matches": matches_list, "last_updated": datetime.now().isoformat()})
        print(f"✅ تم تحديث {len(matches_list)} مباراة بنجاح!")
        
    except Exception as e:
        print(f"خطأ في الفايربيس: {e}")

if __name__ == "__main__":
    data = get_365scores_matches()
    update_firebase(data)
