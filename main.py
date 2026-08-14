import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
import sys

sys.stdout.reconfigure(encoding='utf-8')

# الاتصال بفايربيس
try:
    firebase_key_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
    if firebase_key_json:
        cred_dict = json.loads(firebase_key_json)
        cred = credentials.Certificate(cred_dict)
    else:
        cred = credentials.Certificate("firebase_key.json")
        
    firebase_admin.initialize_app(cred)
    db = firestore.client()
except Exception as e:
    print(f"خطأ في الاتصال: {e}")
    sys.exit(1)

# بيانات اليوم الثابتة لإنقاذ الموقف (بدون استخدام الـ API)
final_data = {
    "last_updated": "2026-08-15",
    "matches": [
        {
            "home_team": "التعاون", "home_team_logo": "https://media.api-sports.io/football/teams/164.png", 
            "away_team": "الخليج", "away_team_logo": "https://media.api-sports.io/football/teams/160.png",
            "match_time": "07:15 م", "league_name": "الدوري السعودي للمحترفين",
            "channels": [{"name": "ثمانية الرياضية", "commentator": "غير محدد"}]
        },
        {
            "home_team": "الاتحاد", "home_team_logo": "https://media.api-sports.io/football/teams/157.png", 
            "away_team": "الخلود", "away_team_logo": "https://media.api-sports.io/football/teams/162.png",
            "match_time": "09:00 م", "league_name": "الدوري السعودي للمحترفين",
            "channels": [{"name": "ثمانية الرياضية", "commentator": "غير محدد"}]
        },
        {
            "home_team": "النصر", "home_team_logo": "https://media.api-sports.io/football/teams/153.png", 
            "away_team": "الفتح", "away_team_logo": "https://media.api-sports.io/football/teams/154.png",
            "match_time": "09:00 م", "league_name": "الدوري السعودي للمحترفين",
            "channels": [{"name": "ثمانية الرياضية", "commentator": "غير محدد"}]
        },
        {
            "home_team": "ألافيس", "home_team_logo": "https://media.api-sports.io/football/teams/529.png", 
            "away_team": "خيتافي", "away_team_logo": "https://media.api-sports.io/football/teams/546.png",
            "match_time": "08:30 م", "league_name": "الدوري الإسباني",
            "channels": [{"name": "beIN Sports", "commentator": "غير محدد"}]
        },
        {
            "home_team": "إشبيلية", "home_team_logo": "https://media.api-sports.io/football/teams/536.png", 
            "away_team": "رايو فايكانو", "away_team_logo": "https://media.api-sports.io/football/teams/720.png",
            "match_time": "10:30 م", "league_name": "الدوري الإسباني",
            "channels": [{"name": "beIN Sports", "commentator": "غير محدد"}]
        }
    ]
}

# الرفع لفايربيس
db.collection('daily_matches').document('daily_matches').set(final_data)
print("تم رفع مباريات اليوم يدوياً بنجاح! اذهب لتطبيقك وستجدها معروضة للمشاهدين.")
