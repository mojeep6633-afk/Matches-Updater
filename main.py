import os
import json
from playwright.sync_api import sync_playwright
import firebase_admin
from firebase_admin import credentials, storage, firestore

# 1. إعداد الاتصال بفايربيس
def initialize_firebase():
    # استدعاء مفتاح فايربيس من إعدادات GitHub أو محلياً
    firebase_key = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if firebase_key:
        cred_dict = json.loads(firebase_key)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("firebase_key.json")
    
    # ضع هنا رابط الـ Storage الخاص بمشروعك (تأخذه من لوحة تحكم فايربيس)
    # مثال: 'titanium-app-1234.appspot.com'
    bucket_name = 'ضع_اسم_مساحة_التخزين_هنا.appspot.com'
    
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred, {'storageBucket': bucket_name})
    
    return firestore.client(), storage.bucket()

def capture_and_upload():
    db, bucket = initialize_firebase()
    image_filename = 'daily_matches.png'

    print("بدء تشغيل المتصفح الوهمي...")
    
    with sync_playwright() as p:
        # فتح متصفح مخفي
        browser = p.chromium.launch(headless=True)
        
        # 2. إعداد شاشة جوال وهمية بدقة عالية جداً (السر في عدم تكسر الصورة)
        context = browser.new_context(
            viewport={'width': 450, 'height': 800}, # عرض جوال لترتيب نظيف
            device_scale_factor=3, # مضاعفة البكسلات 3 مرات لدقة 4K
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        print("جاري الدخول إلى موقع في الجول...")
        page.goto('https://www.filgoal.com/matches/', wait_until='networkidle')
        
        # 3. عملية التنظيف البرمجي الذكية (إخفاء المشتتات)
        print("جاري تنظيف الصفحة من الإعلانات ومشغلات الفيديو...")
        page.evaluate('''
            () => {
                // حذف كل الإعلانات (Banners & Ads)
                document.querySelectorAll('iframe, .ad, .ads, [id^="div-gpt-ad"]').forEach(el => el.remove());
                
                // حذف مشغلات الفيديو تماماً من وسط الجدول
                document.querySelectorAll('.video-player, video, .media-player, .stream-box').forEach(el => el.remove());
                
                // حذف الشريط العلوي (Header) والسفلي (Footer) لتبقى المباريات فقط
                document.querySelectorAll('header, footer, .navbar, .app-download-banner').forEach(el => el.remove());
            }
        ''')
        
        # الانتظار ثانية واحدة للتأكد من اختفاء العناصر
        page.wait_for_timeout(1000)
        
        # 4. التقاط صورة كاملة للجدول النظيف
        print("جاري التقاط الصورة فائقة الدقة...")
        page.screenshot(path=image_filename, full_page=True)
        browser.close()

    # 5. رفع الصورة إلى Firebase Storage
    print("جاري رفع الصورة إلى فايربيس...")
    blob = bucket.blob(image_filename)
    # إضافة صلاحية لكي يتمكن التطبيق من قراءة الصورة
    blob.upload_from_filename(image_filename, content_type='image/png')
    blob.make_public()
    image_url = blob.public_url
    
    # 6. تحديث رابط الصورة في قاعدة البيانات Firestore ليقرأها التطبيق
    print("جاري تحديث قاعدة البيانات بالرابط الجديد...")
    db.collection('daily_matches').document('schedule').set({
        'image_url': image_url,
        'last_updated': firestore.SERVER_TIMESTAMP
    })
    
    print(f"تمت العملية بنجاح! الرابط الجديد للصورة: {image_url}")

if __name__ == '__main__':
    capture_and_upload()
