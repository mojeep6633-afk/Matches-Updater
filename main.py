import os
from playwright.sync_api import sync_playwright

def capture_and_save_locally():
    image_filename = 'daily_matches.png'

    print("بدء تشغيل المتصفح الوهمي...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # إعداد شاشة وهمية
        context = browser.new_context(
            viewport={'width': 450, 'height': 2000},
            device_scale_factor=3,
            user_agent='Mozilla/5.0 (Linux; Android 11) AppleWebKit/537.36 KHTML Mobile Safari'
        )
        
        page = context.new_page()
        print("جاري الدخول إلى موقع في الجول...")
        
        page.goto('https://www.filgoal.com/matches/', timeout=60000, wait_until='load')
        page.wait_for_timeout(4000)
        
        print("جاري تنظيف الصفحة وإزالة الزوائد...")
        page.evaluate('''
            () => {
                const selectorsToRemove = [
                    'iframe', '.ad', '.ads', '[id^="div-gpt-ad"]', 
                    'header', 'footer', '.navbar', '.app-download-banner', 
                    '.video-player', 'video', '.media-player', '.stream-box'
                ];
                document.querySelectorAll(selectorsToRemove.join(',')).forEach(el => el.remove());
                
                // توحيد الخلفية وإزالة المساحات البيضاء العلوية
                document.body.style.backgroundColor = '#1E1E1E';
                document.documentElement.style.backgroundColor = '#1E1E1E';
            }
        ''')
        
        print("جاري النقر المباشر على زر إظهار المباريات الكاملة...")
        try:
            # محاولة النقر على زر السهم مباشرة عبر محدد دقيق في Playwright
            # البحث عن أي عنصر يحتوي على أيقونة السهم أو كلمة المزيد في قسم المباريات
            expand_btn = page.locator('.matches-day-container svg, .matches-day-container .ico-arrow-down, [class*="arrow"]').last
            if expand_btn.is_visible():
                expand_btn.click()
                print("تم النقر على زر التوسيع بنجاح!")
            else:
                # طريقة بديلة عبر JavaScript في حال لم يظهر عبر القائمة
                page.evaluate('''
                    () => {
                        let svgs = document.querySelectorAll('.matches-day-container svg');
                        if (svgs.length > 0) {
                            svgs[svgs.length - 1].dispatchEvent(new MouseEvent('click', { bubbles: true }));
                        }
                    }
                ''')
        except Exception as e:
            print(f"ملاحظة أثناء محاولة النقر: {e}")
            
        # انتظار حتى تفتح القائمة بالكامل وتظهر كل المباريات
        page.wait_for_timeout(4000)
        
        print("جاري التقاط صورة جدول المباريات الكامل...")
        try:
            matches_box = page.locator('.matches-day-container').first
            matches_box.screenshot(path=image_filename)
        except Exception as e:
            print(f"حدث خطأ في تحديد الصندوق، التقاط الشاشة العامة: {e}")
            page.screenshot(path=image_filename, full_page=True)
            
        browser.close()
        
    print(f"تم التقاط الصورة بنجاح وحفظها باسم: {image_filename}")

if __name__ == '__main__':
    capture_and_save_locally()
