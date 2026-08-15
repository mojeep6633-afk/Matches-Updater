import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تصوير الجدول والتخلص النهائي من الإعلانات والنوافذ...")
    
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
        
        # الانتظار قليلاً لتحميل العناصر ثم تنفيذ التنظيف المكثف
        page.wait_for_timeout(4000)
        
        print("تنظيف العناصر وإزالة الإعلانات البيضاء وزر اكتشف المزيد...")
        page.evaluate('''
            () => {
                // دالة شاملة لمسح كافة الإعلانات، النتائج، الدقائق، والنوافذ المتكررة
                const cleanPage = () => {
                    const unwantedSelectors = [
                        '.match-score', '.match-minute', '.match-state', 
                        '.live-label', '.ico-clock', '.m-status',
                        'header', 'footer', '.app-banner-wrapper', 
                        '.ads-container', 'iframe', 'nav',
                        '[class*="banner"]', '[class*="footer"]', 
                        '[class*="load-more"]', '[id*="load-more"]',
                        '[class*="ad"]', '[id*="ad"]', '.popup', '.overlay'
                    ];
                    
                    unwantedSelectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(el => el.remove());
                    });

                    // إزالة أي عناصر تحتوي على جمل مزعجة مثل "اكتشف المزيد"
                    document.querySelectorAll('div, a, span, button').forEach(el => {
                        if (el.children.length === 0 && el.textContent.includes('اكتشف المزيد')) {
                            el.remove();
                        }
                    });
                };

                // تشغيل التنظيف فوراً
                cleanPage();
                
                // إعادة التنظيف عدة مرات لضمان عدم ظهور أي إعلان متأخر
                setTimeout(cleanPage, 1000);
                setTimeout(cleanPage, 2000);
            }
        ''')
        
        page.wait_for_timeout(2000)
        
        print("جاري التقاط الصورة النظيفة...")
        try:
            main_content = page.locator('.matches-score-body, .container, main').first
            if main_content.is_visible():
                main_content.screenshot(path=image_filename)
            else:
                page.screenshot(path=image_filename)
        except:
            page.screenshot(path=image_filename)
            
        browser.close()
        
    print(f"تم التقاط الصورة وتصفيتها بنجاح تام!")

if __name__ == '__main__':
    capture_and_save_locally()
