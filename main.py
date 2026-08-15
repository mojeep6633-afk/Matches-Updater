import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تصوير الجدول (بتوقيت السعودية)...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # إضافة Timezone لتوقيت السعودية لضمان دقة الساعة
        context = browser.new_context(
            viewport={'width': 450, 'height': 3000},
            timezone_id='Asia/Riyadh', 
            device_scale_factor=2,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        )
        
        page = context.new_page()
        page.goto('https://mobile.btolat.com/matches-score', timeout=60000, wait_until='load')
        page.wait_for_timeout(5000)
        
        print("جاري التنظيف الشامل...")
        page.evaluate('''
            () => {
                // إخفاء كافة العناصر التي تحمل نتائج أو دقائق أو حالة
                const elementsToHide = [
                    '.match-score', '.match-minute', '.match-state', 
                    '.live-label', '.ico-clock', '.m-status',
                    '.app-banner-wrapper', '.ads-container'
                ];
                
                elementsToHide.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => el.style.display = 'none');
                });
                
                // إخفاء أي أيقونات إضافية في صف المباراة
                document.querySelectorAll('svg').forEach(el => {
                    if (el.closest('.match-info')) el.style.display = 'none';
                });
            }
        ''')
        
        page.wait_for_timeout(2000)
        
        print("جاري التقاط الصورة...")
        page.screenshot(path=image_filename, full_page=True)
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح وبتوقيت مكة المكرمة!")

if __name__ == '__main__':
    capture_and_save_locally()
