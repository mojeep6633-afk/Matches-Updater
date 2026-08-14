import os
import json
from playwright.sync_api import sync_playwright
import firebase_admin
from firebase_admin import credentials, storage, firestore

def initialize_firebase():
    firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if firebase_key:
        cred_dict = json.loads(firebase_key)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("firebase_key.json")
    
    # تأكد من وضع رابط مساحة التخزين الخاصة بك هنا
    bucket_name = 'ضع_اسم_مساحة_التخزين_هنا.appspot.com'
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {'storageBucket': bucket_name})
    
    return firestore.client(), storage.bucket()

def capture_and_upload():
    db, bucket = initialize_firebase()
    image_filename = 'daily_matches.png'

    print("بدء تشغيل المتصفح الوهمي...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            viewport={'width': 450, 'height': 800},
            device_scale_factor=3,
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        print("جاري الدخول إلى موقع في الجول...")
        
        # التعديل هنا: استخدام 'load' وزيادة وقت الانتظار إلى 60 ثانية
        page.goto('https://www.filgoal.com/matches/', timeout=60000, wait_until='load')
        
        # انتظار إضافي لمدة 3 ثواني لضمان ظهور الجدول بالكامل قبل التنظيف
        page.wait_for_timeout(3000)
        
        print("جاري تنظيف الصفحة من الإعلانات ومشغلات الفيديو...")
        page.evaluate('''
            () => {
                document.querySelectorAll('iframe, .ad, .ads, [id^="div-gpt-ad"]').forEach(el => el.remove());
                document.querySelectorAll('.video-player, video, .media-player, .stream-box').forEach(el => el.remove());
                document.querySelectorAll('header, footer, .navbar, .app-download-banner').forEach(el => el.remove());
            }
        ''')
        
        page.wait_for_timeout(1000)
        
        print("جاري التقاط الصورة فائقة الدقة...")
        page.screenshot(path=image_filename, full_page=True)
        browser.close()

    print("جاري رفع الصورة إلى فايربيس...")
    blob = bucket.blob(image_filename)
    blob.upload_from_filename(image_filename, content_type='image/png')
    blob.make_public()
    image_url = blob.public_url
    
    print("جاري تحديث قاعدة البيانات بالرابط الجديد...")
    db.collection('daily_matches').document('schedule').set({
        'image_url': image_url,
        'last_updated': firestore.SERVER_TIMESTAMP
    })
    
    print(f"تمت العملية بنجاح! الرابط الجديد للصورة: {image_url}")

if __name__ == '__main__':
    capture_and_upload()
