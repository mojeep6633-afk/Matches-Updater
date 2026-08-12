from apify_client import ApifyClient

# 1. ضع مفتاح الأمان (API Token) الخاص بحسابك في Apify هنا
APIFY_TOKEN = "ضع_مفتاح_الأمان_الخاص_بك_هنا"
client = ApifyClient(APIFY_TOKEN)

# 2. إعداد المدخلات مع تفعيل البروكسي لمصر أو السعودية كمثال
run_input = {
    "sport": "football",
    "category": "matches",
    "date": "today",
    "maxItems": 50,
    
    # --- إعدادات البروكسي الجديدة ---
    "proxyConfiguration": {
        "useApifyProxy": True,
        "apifyProxyGroups": [
            "RESIDENTIAL" # استخدام بروكسي سكني لضمان عدم حظره من 365Scores
        ],
        "apifyProxyCountry": "SA" # كود الدولة: SA للسعودية، EG لمصر، AE للإمارات
    }
}

print("جاري تشغيل الكاشف باستخدام بروكسي عربي لجلب المعلقين والقنوات...")

try:
    # 3. تشغيل الأداة
    run = client.actor("apify/365scores-sports-data-scraper").call(run_input=run_input)
    dataset_items = client.dataset(run["defaultDatasetId"]).list().items

    # 4. طباعة النتائج تشمل الشعارات والقنوات والمعلقين
    for match in dataset_items:
        home_team = match.get("homeTeam", {}).get("name", "الفريق المضيف")
        home_logo = match.get("homeTeam", {}).get("logoUrl", "") # رابط شعار الفريق
        
        away_team = match.get("awayTeam", {}).get("name", "الفريق الضيف")
        away_logo = match.get("awayTeam", {}).get("logoUrl", "") # رابط شعار الفريق المنافس
        
        # جلب القنوات والمعلقين (تظهر بفضل البروكسي العربي)
        broadcasters = match.get("broadcasters", []) # قائمة القنوات الناقلة
        channels = ", ".join([b.get("name") for b in broadcasters]) if broadcasters else "غير معلن"
        
        commentator = match.get("commentator", "غير محدد") # اسم المعلق
        
        print(f"⚽ {home_team} VS {away_team}")
        print(f"🖼️ شعار المضيف: {home_logo}")
        print(f"🖼️ شعار الضيف: {away_logo}")
        print(f"📺 القنوات الناقلة: {channels}")
        print(f"🎙️ المعلق: {commentator}")
        print("-" * 50)

except Exception as e:
    print(f"حدث خطأ: {e}")
