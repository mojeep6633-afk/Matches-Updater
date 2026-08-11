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
        
        # كتابة وثيقة اختبار إجبارية للتأكد من الاتصال فوراً
        db.collection("koora").document("test_connection_now").set({
            "status": "Success",
            "time": firestore.SERVER_TIMESTAMP
        })
        print("تمت كتابة وثيقة الاختبار في فايربيس بنجاح تام!")
        
    except Exception as e:
        print(f"فشل الاتصال أو الكتابة في فايربيس بسبب الخطأ التالي: {e}")
