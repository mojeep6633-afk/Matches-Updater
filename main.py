import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تصوير الجدول بشكل منسق ومحدد...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            viewport={'width': 450, 'height': 1200}, # ارتفاع متوازن للشاشة
            timezone_id='Asia/Riyadh',
            device_scale_factor=2,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        )
        
        page = context.new_page()
        page.goto('https://mobile.btolat.com/matches-score', timeout=60000, wait_until='load')
        page.wait_for_timeout(5000)
        
        print("جاري تنظيف العناصر غير المرغوبة...")
        page.evaluate('''
            () => {
                const elementsToHide = [
                    '.match-score', '.match-minute', '.match-state', 
                    '.live-label', '.ico-clock', '.m-status',
                    '.app-banner-wrapper', '.ads-container', 'header', 'footer'
                ];
                
                elementsToHide.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => {
                        el.style.display = 'none';
                        el.style.height = '0';
                        el.style.margin = '0';
                    });
                });
            }
        ''')
        
        page.wait_for_timeout(2000)
        
        print("جاري التقاط الحاوية الرئيسية فقط...")
        try:
            # محاولة تصوير قسم المباريات الرئيسي فقط بدلاً من الصفحة بأكملها
            main_content = page.locator('.matches-score-body, .container, main').first
            if main_content.is_visible():
                main_content.screenshot(path=image_filename)
            else:
                page.screenshot(path=image_filename)
        except:
            page.screenshot(path=image_filename)
            
        browser.close()
        
    print(f"تم التقاط الصورة باحترافية وبدون مساحات فارغة!")

if __name__ == '__main__':
    capture_and_save_locally()
