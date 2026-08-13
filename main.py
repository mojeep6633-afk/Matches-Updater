import requests

url = "https://v3.football.api-sports.io/fixtures"
API_KEY = "12d594efcd4cf9df22a2dba5067a8254"

headers = {
    'x-apisports-key': API_KEY
}

params = {
    'league': '307',       # الدوري السعودي للمحترفين
    'season': '2025',      # الموسم الحالي المعتمد في المنصة حالياً
    'status': 'NS'         # المباريات القادمة فقط (Not Started)
}

try:
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if response.status_code == 200 and data.get("response"):
        fixtures_list = data["response"]
        
        print(f"=== جدول مباريات الدوري السعودي للمحترفين ===\n")
        print(f"{'التاريخ':<12} | {'الجولة':<15} | {'صاحب الأرض':<20} | {'الضيف':<20}")
        print("-" * 75)
        
        for match in fixtures_list[:15]:
            date = match["fixture"]["date"].split("T")[0]
            round_name = match["league"]["round"]
            home_team = match["teams"]["home"]["name"]
            away_team = match["teams"]["away"]["name"]
            
            print(f"{date:<12} | {round_name:<15} | {home_team:<20} | {away_team:<20}")
            
    else:
        print("فشل جلب البيانات أو القائمة فارغة. تأكد من صحة البيانات.")
        
except Exception as e:
    print(f"خطأ: {e}")
