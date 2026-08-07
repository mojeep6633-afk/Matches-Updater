import requests
from datetime import datetime
import pytz

def get_todays_matches():
    # 1. تحديد تاريخ اليوم بصيغة YYYY-MM-DD
    today_date = datetime.now().strftime('%Y-%m-%d')
    
    # 2. رابط الـ API الخاص بـ FilGoal (هذا مثال لأحد الروابط المستخدمة لديهم)
    url = f"https://api.filgoal.com/api/matches/GetByDate?date={today_date}"
    
    # إضافة ترويسة (Header) حتى لا يتعرف الخادم على الطلب كـ Bot ويرفضه
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        # إرسال الطلب واستقبال البيانات بصيغة JSON
        response = requests.get(url, headers=headers)
        response.raise_for_status() # للتحقق من عدم وجود خطأ في الاتصال
        matches_data = response.json()
        
        # تحديد توقيت مصدر البيانات (القاهرة)
        cairo_tz = pytz.timezone('Africa/Cairo')
        
        clean_matches = []
        
        # 3. المرور على جميع المباريات واستخراج المطلوب فقط
        for match in matches_data:
            # قد تحتاج لتعديل أسماء المفاتيح (Keys) حسب التحديث الأخير لـ API الموقع
            champ_name = match.get('ChampionshipName', 'بطولة غير معروفة')
            home_team = match.get('HomeTeamName', 'فريق 1')
            away_team = match.get('AwayTeamName', 'فريق 2')
            
            # معالجة روابط الشعارات (أحياناً تأتي كمسار نسبي، فنضيف لها الدومين)
            home_logo = match.get('HomeTeamLogoUrl', '')
            if not home_logo.startswith('http'):
                home_logo = f"https://www.filgoal.com{home_logo}"
                
            away_logo = match.get('AwayTeamLogoUrl', '')
            if not away_logo.startswith('http'):
                away_logo = f"https://www.filgoal.com{away_logo}"
                
            channel = match.get('ChannelName', 'غير متوفر')
            commentator = match.get('CommentatorName', 'غير متوفر')
            
            # --- 4. معالجة وتعديل التوقيت حسب جهازك ---
            match_date_str = match.get('Date') # يأتي غالباً بصيغة "2026-08-07T20:00:00"
            
            if match_date_str:
                # تحويل النص إلى كائن وقت
                match_time_obj = datetime.strptime(match_date_str[:19], '%Y-%m-%dT%H:%M:%S')
                
                # إخبار بايثون أن هذا الوقت هو بتوقيت القاهرة
                match_time_cairo = cairo_tz.localize(match_time_obj)
                
                # السحر هنا: دالة astimezone() بدون متغيرات تحول الوقت تلقائياً لتوقيت جهازك الحالي!
                local_match_time = match_time_cairo.astimezone()
                
                # تنسيق الوقت للعرض (مثال: 08:30 PM)
                final_time = local_match_time.strftime('%I:%M %p')
            else:
                final_time = "غير محدد"

            # 5. حفظ البيانات النظيفة في قائمة
            clean_matches.append({
                "بطولة": champ_name,
                "المباراة": f"{home_team} ضد {away_team}",
                "الوقت_المحلي": final_time,
                "القناة": channel,
                "المعلق": commentator,
                "شعار_المضيف": home_logo,
                "شعار_الضيف": away_logo
            })
            
        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

# --- تشغيل السكربت ---
if __name__ == "__main__":
    matches = get_todays_matches()
    
    if matches:
        print(f"تم جلب {len(matches)} مباريات بنجاح:\n" + "="*40)
        for m in matches:
            print(f"🏆 {m['بطولة']}")
            print(f"⚽ {m['المباراة']}")
            print(f"⏰ الوقت: {m['الوقت_المحلي']}")
            print(f"📺 القناة: {m['القناة']} | 🎙️ المعلق: {m['المعلق']}")
            print(f"🖼️ شعار المضيف: {m['شعار_المضيف']}")
            print(f"🖼️ شعار الضيف: {m['شعار_الضيف']}")
            print("-" * 40)
