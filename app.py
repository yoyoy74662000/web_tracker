import os
import time
import datetime
from flask import Flask, render_template, send_file, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import requests

app = Flask(__name__)
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def scrape_top_20(period):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Comment this if debugging
    driver = webdriver.Chrome(options=options)
    driver.get("https://www.moneydj.com/funddj/ya/yp401000.djhtm")
    time.sleep(2)

    header = driver.find_element(By.XPATH, f"//th[contains(text(), '{period}')]")
    if period == "一年":
        header.click()
        header.click()
    else:
        header.click()
    time.sleep(1)

    rows = driver.find_elements(By.CSS_SELECTOR, "#oMainTable tbody tr")
    data = []
    for row in rows[:20]:
        cells = row.find_elements(By.TAG_NAME, "td")
        data.append([cell.text.strip() for cell in cells])
    driver.quit()

    df = pd.DataFrame(data)
    df.columns = [
        " ", "排名", "基金名稱", "基金公司", "日期", "一個月",
        "三個月", "六個月", "一年", "三年", "五年", "十年", "交易"
    ]
    df_filtered = df[["排名", "基金名稱", "基金公司", period]]

    now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"top_20_funds_{period}_{now_str}.xlsx"
    filepath = os.path.join(OUTPUT_DIR, filename)
    df_filtered.to_excel(filepath, index=False)
    return filepath

def send_to_telegram(filepath, caption=None):
    bot_token = "8146020101:AAGVMsYfnFkdKztkpTyAb7Y_dore7WnV0VY"
    chat_id = -4699704695
    if not bot_token or not chat_id:
        return False
    url = f"https://api.telegram.org/bot{bot_token}/sendDocument"
    with open(filepath, "rb") as file:
        files = {"document": file}
        data = {"chat_id": chat_id, "caption": caption}
        response = requests.post(url, data=data, files=files)
    return response.ok

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/download", methods=["POST"])
def download():
    period = request.form.get("period")
    file_path = scrape_top_20(period)
    return send_file(file_path, as_attachment=True)

@app.route("/send", methods=["POST"])
def send():
    period = request.form.get("period")
    file_path = scrape_top_20(period)
    success = send_to_telegram(file_path, caption=f"Top 20 funds for {period}")
    # if success:
    #     return f"✅ Sent to Telegram successfully!"
    # else:
    #     return f"❌ Failed to send to Telegram. Check bot token & chat ID."
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
