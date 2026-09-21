import os
import sys
import requests

# 1. 讀取 Telegram 設定 (符合規格 7)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("錯誤：未設定 TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID！")
    sys.exit(1)

# 桃園市桃園區座標
LATITUDE = 24.9936
LONGITUDE = 121.3010

def fetch_taoyuan_weather_and_aqi():
    """使用 Open-Meteo API 抓取桃園的當日氣象與 AQI 資料"""
    try:
        # 取得氣象資料 (每日最高溫與最高降雨機率)
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={LATITUDE}&longitude={LONGITUDE}"
            f"&daily=temperature_2m_max,precipitation_probability_max"
            f"&timezone=Asia%2FTaipei"
        )
        weather_res = requests.get(weather_url, timeout=10)
        weather_res.raise_for_status()
        weather_data = weather_res.json()["daily"]

        # 取得空氣品質資料 (當日小時預報中的最高 US AQI)
        air_url = (
            f"https://air-quality-api.open-meteo.com/v1/air-quality?"
            f"latitude={LATITUDE}&longitude={LONGITUDE}"
            f"&hourly=us_aqi"
            f"&forecast_days=1"
            f"&timezone=Asia%2FTaipei"
        )
        air_res = requests.get(air_url, timeout=10)
        air_res.raise_for_status()
        air_data = air_res.json()["hourly"]

        # 解析桃園當日最高數據
        max_temp = weather_data["temperature_2m_max"][0]
        max_rain_prob = weather_data["precipitation_probability_max"][0]
        
        # 過濾 None 後計算當日 AQI 最高值
        aqi_list = [val for val in air_data["us_aqi"] if val is not None]
        max_aqi = max(aqi_list) if aqi_list else 0

        return {
            "max_temp": max_temp,
            "rain_prob": max_rain_prob,
            "aqi": max_aqi
        }
    except Exception as e:
        print(f"抓取桃園資料失敗: {e}")
        sys.exit(1)

def build_alert_message(data):
    """依據作業規格生成警報內容"""
    max_temp = data["max_temp"]
    rain_prob = data["rain_prob"]
    aqi = data["aqi"]

    alerts = []

    # 規格 3: 降雨機率達 60% 時提醒攜帶雨傘
    if rain_prob >= 60:
        alerts.append("🌧️ 降雨機率達 60% 以上，請記得攜帶雨傘！")

    # 規格 4: 最高溫度達 33°C 時提醒防曬與補充水分
    if max_temp >= 33:
        alerts.append("☀️ 最高溫達 33°C 以上，請注意防曬並多補充水分！")

    # 規格 5: AQI 達 100 時提醒配戴口罩
    if aqi >= 100:
        alerts.append("😷 空氣品質 AQI 達 100 以上，建議配戴口罩！")

    # 規格 6: 所有條件正常時，顯示適合外出通勤
    if not alerts:
        alerts.append("✅ 今日各項條件正常，適合外出通勤！")

    message = (
        f"🚲 【桃園智慧通勤風險通知】\n"
        f"📍 今日桃園預報：最高溫 {max_temp}°C | 最高降雨機率 {rain_prob}% | 最高 AQI {aqi}\n"
        f"------------------------------------\n"
        + "\n".join(alerts)
    )
    return message

def send_telegram_alert(text):
    """發送訊息至 Telegram Bot"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text
    }
    response = requests.post(url, json=payload, timeout=10)
    if response.status_code == 200:
        print("桃園通勤通知發送成功！")
    else:
        print(f"Telegram 發送失敗 ({response.status_code}): {response.text}")

if __name__ == "__main__":
    taoyuan_data = fetch_taoyuan_weather_and_aqi()
    alert_msg = build_alert_message(taoyuan_data)
    send_telegram_alert(alert_msg)
