import json
import os
from datetime import datetime
import firebase_admin
import pytz
import requests
from bs4 import BeautifulSoup
from firebase_admin import credentials, firestore

def get_todays_matches():
    today_date = datetime.now().strftime("%Y-%m-%d")
    url = f"https://www.filgoal.com/matches/?date={today_date}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        
        cairo_tz = pytz.timezone("Africa/Cairo")
        riyadh_tz = pytz.timezone("Asia/Riyadh")
        
        clean_matches = []
        
        important_leagues = [
            "دوري روشن السعودي", "دوري أبطال أوروبا", "دوري أبطال آسيا",
            "الدوري الإنجليزي", "الدوري الإسباني", "الدوري الإيطالي",
            "مباريات دولية", "دوري أبطال آسيا للنخبة", "كأس العالم",
            "دوري أبطال إفريقيا", "ودي", "ودية", "مباريات ودية",
            "ودية أندية", "مباريات ودية - أندية", 
            "كأس الملك", "كأس خادم الحرمين الشريفين"
        ]
        
        # البحث عن كل صناديق البطولات في الصفحة
        champ_blocks = soup.find_all("div", class_="mc-block")
        
        for block in champ_blocks:
            champ_title_tag = block.find("h6")
            if not champ_title_tag:
                continue
            champ_name = champ_title_tag.text.strip()
            
            # التحقق من أن البطولة من ضمن الدوريات المطلوبة
            if not any(league in champ_name for league in important_leagues):
                continue
                
            matches = block.find_all("div", class_="cin_cntnr")
            
            for match in matches:
                # سحب أسماء الفرق
                team_a_tag = match.find("div", class_="f")
                team_b_tag = match.find("div", class_="s")
                
                if not team_a_tag or not team_b_tag:
                    continue
                    
                home_team = team_a_tag.find("strong").text.strip() if team_a_tag.find("strong") else "فريق 1"
                away_team = team_b_tag.find("strong").text.strip() if team_b_tag.find("strong") else "فريق 2"
                
                # سحب الشعارات
                home_logo_tag = team_a_tag.find("img")
                away_logo_tag = team_b_tag.find("img")
                
                home_logo = home_logo_tag["src"] if home_logo_tag and "src" in home_logo_tag.attrs else ""
                if home_logo and home_logo.startswith("//"): home_logo = f"https:{home_logo}"
                
                away_logo = away_logo_tag["src"] if away_logo_tag and "src" in away_logo_tag.attrs else ""
                if away_logo and away_logo.startswith("//"): away_logo = f"https:{away_logo}"
                
                # سحب وقت المباراة وتحويله لتوقيت السعودية
                match_time_tag = match.find("div", class_="match-time")
                match_time_str = match_time_tag.text.strip() if match_time_tag else ""
                
                final_time = ""
                if match_time_str and ":" in match_time_str:
                    try:
                        time_obj = datetime.strptime(match_time_str, "%H:%M").time()
                        match_datetime = datetime.combine(datetime.strptime(today_date, "%Y-%m-%d"), time_obj)
                        match_time_cairo = cairo_tz.localize(match_datetime)
                        local_match_time = match_time_cairo.astimezone(riyadh_tz)
                        final_time = local_match_time.strftime("%Y-%m-%dT%H:%M:%S+03:00")
                    except:
                        final_time = f"{today_date}T{match_time_str}:00+03:00"
                
                # سحب القناة والمعلق
                channel = "غير متوفر"
                commentator = ""
                
                match_aux = match.find("div", class_="match-aux")
                if match_aux:
                    channel_icon = match_aux.find("i", class_="icon-tv")
                    if channel_icon and channel_icon.parent:
                        channel = channel_icon.parent.text.strip()
                    
                    mic_icon = match_aux.find("i", class_="icon-mic")
                    if mic_icon and mic_icon.parent:
                        commentator = mic_icon.parent.text.strip()
                        
                clean_matches.append({
                    "league_name": champ_name,
                    "home_team": home_team,
                    "away_team": away_team,
                    "match_time": final_time,
                    "home_team_logo": home_logo,
                    "away_team_logo": away_logo,
                    "channels": [
                        {
                            "name": channel,
                            "commentator": commentator
                        }
                    ]
                })
                
        return clean_matches

    except Exception as e:
        print(f"حدث خطأ أثناء جلب البيانات: {e}")
        return None

def update_firebase(matches_list):
    if not matches_list:
        print("لا توجد مباريات مهمة اليوم في الموقع.")
        return

    firebase_cert_string = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if not firebase_cert_string:
        print("خطأ: لم يتم العثور على مفتاح فايربيس السري في المتغيرات")
        return

    firebase_cert = json.loads(firebase_cert_string)
    cred = credentials.Certificate(firebase_cert)

    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)

    db = firestore.client()
    
    doc_ref = db.collection("koora").document("daily_matches")
    doc_ref.set({"matches": matches_list})

    print(f"تم تحديث فايربيس بنجاح بـ {len(matches_list)} مباراة!")

if __name__ == "__main__":
    print("بدأ سحب وتجهيز جدول المباريات عبر الواجهة المباشرة...")
    todays_matches = get_todays_matches()
    update_firebase(todays_matches)
