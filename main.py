import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تصوير الجدول بدقة تامة للحفاظ على الشعارات والمعلقين...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            viewport={'width': 450, 'height': 2000},
            timezone_id='Asia/Riyadh',
            device_scale_factor=2,
            user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        )
        
        page = context.new_page()
        page.goto('https://mobile.btolat.com/matches-score', timeout=60000, wait_until='load')
        page.wait_for_timeout(5000)
        
        print("تطبيق الفلترة الدقيقة (إخفاء النتائج والوقت المتغير فقط)...")
        page.evaluate('''
            () => {
                // حقن كود CSS مباشر لإخفاء النتائج اللحظية والدقائق وحالة المباراة فقط
                // مع ترك الشعارات، الأسماء، القنوات والمعلقين تعمل بشكل كامل
                const style = document.createElement('style');
                style.innerHTML = `
                    .match-score, .match-minute, .match-state, .live-label {
                        visibility: hidden !important;
                    }
                `;
                document.head.appendChild(style);
            }
        ''')
        
        page.wait_for_timeout(3000)
        
        print("جاري التقاط الصورة الكاملة والواضحة...")
        # التقاط الصفحة بالكامل لضمان عدم قص أي جزء من الجدول أو الشعارات
        page.screenshot(path=image_filename, full_page=True)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح تام والشعارات موجودة!")

if __name__ == '__main__':
    capture_and_save_locally()
