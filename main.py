name: Update Matches Daily

on:
  workflow_dispatch:
  schedule:
    # يشتغل تلقائياً كل يوم الساعة 00:01 ليلاً بتوقيت جرينتش
    - cron: '1 0 * * *'

jobs:
  run-script:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install playwright
          python -m playwright install chromium
          
      - name: Run python main.py
        env:
          PYTHONIOENCODING: 'utf-8'
        run: python main.py

      - name: Commit and push updated image
        run: |
          git config --global user.name "GitHub Actions Bot"
          git config --global user.email "actions@github.com"
          git add daily_matches.png
          git commit -m "Auto-update daily matches image for new day" || exit 0
          git push
