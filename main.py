import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تشغيل المتصفح الوهمي...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # إعداد شاشة جوال وهمية بدقة عالية جداً
        context = browser.new_context(
            viewport={'width': 450, 'height': 800},
            device_scale_factor=3,
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        print("جاري الدخول إلى موقع في الجول...")
        
        page.goto('https://www.filgoal.com/matches/', timeout=60000, wait_until='load')
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
        
        print("جاري تحديد جدول المباريات وتصويره بدقة...")
        try:
            # محاولة التقاط صندوق المباريات فقط لتجنب الصور الزائدة في الأسفل
            matches_box = page.locator('.matches-day-container').first
            matches_box.screenshot(path=image_filename)
        except Exception as e:
            print(f"التحديد الدقيق لمשտ الحاوية لم ينجح، جارِ التقاط الصورة العامة: {e}")
            page.screenshot(path=image_filename, full_page=True)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح وحفظها باسم: {image_filename}")

if __name__ == '__main__':
    capture_and_save_locally()
