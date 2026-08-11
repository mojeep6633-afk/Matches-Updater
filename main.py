import os
import json
import requests
from bs4 import BeautifulSoup
import firebase_admin
from firebase_admin import credentials, firestore

def fetch_matches():
    # ضع هنا رابط الموقع الذي تجلب منه المباريات
    url = "رابط_موقع_المباريات_هنا"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    
    matches = []
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # استخرج المباريات حسب تصميم الموقع لديك وأضفها للقائمة
            # مثال افتراضي:
            # for match in soup.find_all('div', class_='match-item'):
            #     matches.append({"title": match.text})
    except Exception as e:
        print(f"خطأ أثناء جلب المباريات: {e}")
        
    return matches

def update_firebase(matches):
    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_cert_string:
        print("خطأ: مفتاح فايربيس غير موجود في إعدادات جيت هاب")
        return

    try:
        firebase_cert = json.loads(firebase_cert_string)
        cred = credentials.Certificate(firebase_cert)

        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)

        db = firestore.client()
        
        # حفظ المباريات في قاعدة البيانات
        db.collection("koora").document("daily_matches").set({
            "matches": matches,
            "last_update": firestore.SERVER_TIMESTAMP
        })
        print("تم تحديث وحفظ المباريات في فايربيس بنجاح تام!")
        
    except Exception as e:
        print(f"فشل الاتصال أو الكتابة في فايربيس بسبب الخطأ التالي: {e}")

if __name__ == "__main__":
    print("جاري بدء جلب المباريات...")
    matches_data = fetch_matches()
    update_firebase(matches_data)
