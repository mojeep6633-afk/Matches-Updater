import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تشغيل المتصفح الوهمي...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # شاشة وهمية طويلة لضمان ظهور كل المباريات وزر التوسيع
        context = browser.new_context(
            viewport={'width': 450, 'height': 2000},
            device_scale_factor=3,
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        print("جاري الدخول إلى موقع في الجول...")
        
        # استخدام 'load' بدلاً من 'networkidle' لتجنب أخطاء الوقت المستقطع
        page.goto('https://www.filgoal.com/matches/', timeout=60000, wait_until='load')
        page.wait_for_timeout(4000) # انتظار إضافي لضمان ظهور العناصر
        
        print("جاري تنظيف الصفحة وإزالة المساحات البيضاء...")
        page.evaluate('''
            () => {
                // إزالة الإعلانات ومشغلات الفيديو
                const selectorsToRemove = [
                    'iframe', '.ad', '.ads', '[id^="div-gpt-ad"]', 
                    'header', 'footer', '.navbar', '.app-download-banner', 
                    '.video-player', 'video', '.media-player', '.stream-box'
                ];
                document.querySelectorAll(selectorsToRemove.join(',')).forEach(el => el.remove());
                
                // مسح المساحات البيضاء العلوية بالكامل وتوحيد الخلفية
                document.body.style.backgroundColor = '#1E1E1E';
                document.documentElement.style.backgroundColor = '#1E1E1E';
                
                let mainWrapper = document.querySelector('.main-wrapper') || document.body;
                if(mainWrapper) {
                    mainWrapper.style.paddingTop = '0';
                    mainWrapper.style.marginTop = '0';
                }
            }
        ''')
        
        page.wait_for_timeout(1500)
        
        print("جاري الضغط على زر القائمة الكاملة...")
        page.evaluate('''
            () => {
                let container = document.querySelector('.matches-day-container');
                if (container) {
                    let lastElement = container.lastElementChild;
                    if (lastElement) {
                        lastElement.click(); 
                    }
                    
                    let svgs = container.querySelectorAll('svg');
                    if (svgs.length > 0) {
                        let btn = svgs[svgs.length - 1].closest('a, div, button');
                        if (btn) btn.click();
                    }
                }
            }
        ''')
        
        # انتظار حتى تفتح القائمة بالكامل
        page.wait_for_timeout(3000)
        
        print("جاري التقاط صورة جدول المباريات الكامل...")
        try:
            matches_box = page.locator('.matches-day-container').first
            matches_box.screenshot(path=image_filename)
        except Exception as e:
            print(f"حدث خطأ في تحديد الصندوق، سيتم التقاط الصفحة: {e}")
            page.screenshot(path=image_filename, full_page=True)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح وحفظها باسم: {image_filename}")

if __name__ == '__main__':
    capture_and_save_locally()
