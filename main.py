import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تصوير الجدول وتنظيف الشاشة بالكامل...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            viewport={'width': 450, 'height': 1200},
            timezone_id='Asia/Riyadh',
            device_scale_factor=2,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        )
        
        page = context.new_page()
        page.goto('https://mobile.btolat.com/matches-score', timeout=60000, wait_until='load')
        page.wait_for_timeout(5000)
        
        print("جاري إزالة الإعلانات، اسم الموقع، النوافذ العشوائية، وحقوق النشر...")
        page.evaluate('''
            () => {
                // قائمة بالعناصر المزعجة المراد إزالتها نهائياً من الصفحة
                const unwantedSelectors = [
                    '.match-score',       // النتائج اللحظية
                    '.match-minute',      // الدقائق
                    '.match-state',       // حالة المباراة (انتهت/لم تبدأ)
                    '.live-label',
                    '.ico-clock',
                    '.m-status',
                    'header',             // الهيدر العلوي (اسم الموقع وشعاره)
                    'footer',             // الفوتر السفلي (جميع الحقوق محفوظة)
                    '.app-banner-wrapper',// إعلان التطبيق العلوي
                    '.ads-container',     // الحاويات الإعلانية
                    'iframe',
                    'nav',
                    '[class*="banner"]',  // أي بنر إعلاني أو ترويجي
                    '[class*="footer"]',  // أي حقوق نشر سفلية
                    '[class*="load-more"]', // زر أو نافذة "اكتشف المزيد"
                    '[id*="load-more"]'
                ];
                
                unwantedSelectors.forEach(selector => {
                    document.querySelectorAll(selector).forEach(el => el.remove());
                });

                // إزالة أي عناصر نصية تحتوي على عبارة "اكتشف المزيد" أو "جميع الحقوق"
                document.querySelectorAll('*').forEach(el => {
                    if (el.children.length === 0 && (el.textContent.includes('اكتشف المزيد') || el.textContent.includes('جميع الحقوق'))) {
                        el.remove();
                    }
                });
            }
        ''')
        
        page.wait_for_timeout(2000)
        
        print("جاري التقاط الصورة النظيفة...")
        # تصوير حاوية المباريات الأساسية فقط لتجنب أي فراغات طولية
        try:
            main_content = page.locator('.matches-score-body, .container, main').first
            if main_content.is_visible():
                main_content.screenshot(path=image_filename)
            else:
                page.screenshot(path=image_filename)
        except:
            page.screenshot(path=image_filename)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح وتصفيتها بالكامل!")

if __name__ == '__main__':
    capture_and_save_locally()
