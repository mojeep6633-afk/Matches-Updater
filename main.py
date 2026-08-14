import requests

# 1. جلب المباريات (أسماء الفرق والشعارات)
url_fixtures = "https://v3.football.api-sports.io/fixtures"
querystring = {"league": "307", "season": "2024"} # 307 هو معرف الدوري السعودي

headers = {
    "x-rapidapi-host": "v3.football.api-sports.io",
    "x-rapidapi-key": "12d594efcd4cf9df22a2dba5067a8254"
}

response = requests.get(url_fixtures, headers=headers, params=querystring)
data = response.json()

# 2. مثال على قراءة أول مباراة والقناة الناقلة لها
if data["response"]:
    first_match = data["response"][0]
    fixture_id = first_match["fixture"]["id"]
    
    # أسماء الفرق
    home_team = first_match["teams"]["home"]["name"]
    away_team = first_match["teams"]["away"]["name"]
    
    # روابط الشعارات
    home_logo = first_match["teams"]["home"]["logo"]
    away_logo = first_match["teams"]["away"]["logo"]
    
    # جلب القناة الناقلة باستخدام Fixture ID
    url_tv = "https://v3.football.api-sports.io/fixtures/tv"
    tv_querystring = {"fixture": str(fixture_id)}
    tv_response = requests.get(url_tv, headers=headers, params=tv_querystring).json()
    
    tv_channels = [tv["tv"]["name"] for tv in tv_response.get("response", [])]
    
    print(f"المباراة: {home_team} ضد {away_team}")
    print(f"شعار المستضيف: {home_logo}")
    print(f"القنوات الناقلة: {', '.join(tv_channels)}")
