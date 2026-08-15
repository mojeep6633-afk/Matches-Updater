import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تشغيل المتصفح الوهمي...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # 1. قمنا بزيادة طول الشاشة الوهمية (2000) لضمان ظهور الزر بدون الحاجة للتمرير
        context = browser.new_context(
            viewport={'width': 450, 'height': 2000},
            device_scale_factor=3,
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        print("جاري الدخول إلى موقع في الجول...")
        
        # 2. ننتظر حتى يكتمل تحميل الصفحة بالكامل (networkidle)
        page.goto('https://www.filgoal.com/matches/', timeout=60000, wait_until='networkidle')
        
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
                
                // 3. مسح المساحات البيضاء العلوية بالكامل وتوحيد الخلفية باللون الأسود لتناسب تطبيقك
                document.body.style.backgroundColor = '#1E1E1E';
                document.documentElement.style.backgroundColor = '#1E1E1E';
                
                let mainWrapper = document.querySelector('.main-wrapper') || document.body;
                if(mainWrapper) {
                    mainWrapper.style.paddingTop = '0';
                    mainWrapper.style.marginTop = '0';
                }
            }
        ''')
        
        page.wait_for_timeout(1000)
        
        print("جاري الضغط على زر القائمة الكاملة...")
        # 4. طريقة صارمة لإجبار السكربت على النقر على السهم الموجود أسفل الجدول
        page.evaluate('''
            () => {
                let container = document.querySelector('.matches-day-container');
                if (container) {
                    // زر التوسيع في موقع في الجول يكون دائماً آخر عنصر داخل الصندوق
                    let lastElement = container.lastElementChild;
                    if (lastElement) {
                        lastElement.click(); 
                    }
                    
                    // تأكيد إضافي عبر البحث عن السهم (SVG)
                    let svgs = container.querySelectorAll('svg');
                    if (svgs.length > 0) {
                        let btn = svgs[svgs.length - 1].closest('a, div, button');
                        if (btn) btn.click();
                    }
                }
            }
        ''')
        
        # انتظار 3 ثوانٍ حتى تفتح القائمة بالكامل بحركتها البطيئة
        page.wait_for_timeout(3000)
        
        print("جاري التقاط صورة جدول المباريات الكامل...")
        try:
            matches_box = page.locator('.matches-day-container').first
            # التقاط صورة للصندوق الصافي بدون هوامش خارجية
            matches_box.screenshot(path=image_filename)
        except Exception as e:
            print(f"حدث خطأ في تحديد الصندوق، سيتم التقاط الصفحة: {e}")
            page.screenshot(path=image_filename, full_page=True)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح وحفظها باسم: {image_filename}")

if __name__ == '__main__':
    capture_and_save_locally()
