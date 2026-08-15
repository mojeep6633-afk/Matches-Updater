import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تصوير موقع بطولات...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            viewport={'width': 450, 'height': 2000},
            device_scale_factor=3,
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        page.goto('https://mobile.btolat.com/matches-score', timeout=60000, wait_until='load')
        page.wait_for_timeout(3000)
        
        print("جاري تنظيف النتائج اللحظية والإبقاء على التوقيت...")
        page.evaluate('''
            () => {
                // إخفاء النتيجة اللحظية فقط (مثل 0-0، 1-0)
                // وإخفاء الدقائق المتغيرة (مثل 55'، استراحة)
                const selectorsToHide = [
                    '.match-score',    // هذه تخفي النتيجة 0-0
                    '.match-minute',   // هذه تخفي 55'
                    '.match-state',    // هذه تخفي كلمة "استراحة" أو "مباشر"
                    '.live-label'      // أي علامة تدل على البث المباشر
                ];
                
                selectorsToHide.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => el.style.display = 'none');
                });
                
                // إزالة الإعلانات
                document.querySelectorAll('iframe, .ads-container').forEach(el => el.remove());
            }
        ''')
        
        page.wait_for_timeout(2000)
        
        print("جاري التقاط الجدول الصافي مع التوقيت...")
        page.screenshot(path=image_filename, full_page=True)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح!")

if __name__ == '__main__':
    capture_and_save_locally()
