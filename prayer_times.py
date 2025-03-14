import tkinter as tk
import requests
import time
import threading
import pygame
import gpsd
from datetime import datetime
from plyer import notification

pygame.mixer.init()

API_URL = "https://8ldbpgh8mh.execute-api.us-east-1.amazonaws.com/prod/location/{lat}/{lon}?date={date}"

# Material Design Colors
COLOR_PRIMARY = "#6200ee"  # Purple
COLOR_PRIMARY_DARK = "#3700b3"  # Dark Purple
COLOR_SECONDARY = "#03dac6"  # Teal
COLOR_BACKGROUND = "#ffffff"  # White
COLOR_SURFACE = "#f5f5f5"  # Light Gray
COLOR_TEXT = "#000000"  # Black
COLOR_TEXT_SECONDARY = "#757575"  # Gray

# Fonts
FONT_TITLE = ("Roboto", 18, "bold")
FONT_SUBTITLE = ("Roboto", 14)
FONT_BODY = ("Roboto", 12)

def get_gps_location():
    try:
        gpsd.connect()
        packet = gpsd.get_current()
        lat = packet.lat
        lon = packet.lon
        location = f"Lat: {lat}, Lon: {lon}"
        print(f"Using GPS Location: {location}")
        return lat, lon, location
    except Exception as e:
        print("GPS failed, falling back to IP-based location...")
        return get_ip_location()

def get_ip_location():
    try:
        response = requests.get("http://ip-api.com/json/")
        data = response.json()
        if data["status"] == "success":
            lat = data["lat"]
            lon = data["lon"]
            location = f"{data['city']}, {data['country']}"
            print(f"Using IP Location: {location}")
            return lat, lon, location
        else:
            return None, None, "Unknown Location"
    except Exception as e:
        print("Error detecting location:", e)
        return None, None, "Unknown Location"

def get_prayer_times():
    lat, lon, location = get_gps_location()
    if lat is None or lon is None:
        return None
    today_unix = int(time.time())  
    url = API_URL.format(lat=lat, lon=lon, date=today_unix)
    try:
        response = requests.get(url)
        data = response.json()
        return {
            "location": location,
            "prayers": {
                "Sehri": data["fajr"],
                "Sunrise": data["sunrise"],
                "Dhuhr": data["dhuhr"],
                "Asr": data["asr"],
                "Maghrib": data["maghrib"],
                "Isha": data["isha"],
                "Iftar": data["sunset"],
            }
        }
    except Exception as e:
        print("Error fetching prayer times:", e)
        return None

def send_notification(prayer):
    notification.notify(
        title="Prayer Time Reminder",
        message=f"It's time for {prayer}!",
        app_icon=None,
        timeout=10
    )

def play_azan():
    try:
        pygame.mixer.music.load("azan.mp3")
        pygame.mixer.music.play()
    except Exception as e:
        print("Error playing Azan:", e)

def check_prayer_time():
    global prayer_times
    while True:
        now = datetime.now().strftime("%H:%M")
        for prayer, time in prayer_times["prayers"].items():
            if time == now:
                print(f"Time for {prayer}!")
                if prayer != "Sunrise":
                    play_azan()
                    send_notification(prayer)
                highlight_prayer(prayer)
        time.sleep(60)

def highlight_prayer(prayer):
    for label in prayer_labels.values():
        label.config(bg=COLOR_SURFACE)  
    if prayer in prayer_labels:
        if prayer == "Sehri":
            prayer_labels[prayer].config(bg=COLOR_SECONDARY, fg=COLOR_TEXT)
        else:
            prayer_labels[prayer].config(bg=COLOR_PRIMARY, fg=COLOR_BACKGROUND)

def update_prayer_times():
    global prayer_times, prayer_labels
    while True:
        new_prayer_times = get_prayer_times()
        if new_prayer_times:
            prayer_times = new_prayer_times
            location_label.config(text=f"Location: {prayer_times['location']}")
            for prayer, time in prayer_times["prayers"].items():
                if prayer in prayer_labels:
                    prayer_labels[prayer].config(text=time)
        time.sleep(10)

# Main Application
root = tk.Tk()
root.title("Prayer Times - Prepared by Md Ariful Islam")
root.geometry("400x500")
root.configure(bg=COLOR_BACKGROUND)
root.attributes("-topmost", True)  

# Title Label
title_label = tk.Label(root, text="Prayer Times", font=FONT_TITLE, bg=COLOR_BACKGROUND, fg=COLOR_TEXT)
title_label.pack(pady=20)

# Location Label
location_label = tk.Label(root, text="Fetching location...", font=FONT_SUBTITLE, bg=COLOR_BACKGROUND, fg=COLOR_TEXT_SECONDARY)
location_label.pack(pady=5)

# Table Frame
table_frame = tk.Frame(root, bg=COLOR_BACKGROUND)
table_frame.pack(pady=10)

# Table Headers
header1 = tk.Label(table_frame, text="Prayer Name", font=FONT_BODY, bg=COLOR_SURFACE, fg=COLOR_TEXT, width=15, padx=10, pady=5)
header1.grid(row=0, column=0, padx=5, pady=5)

header2 = tk.Label(table_frame, text="Time", font=FONT_BODY, bg=COLOR_SURFACE, fg=COLOR_TEXT, width=10, padx=10, pady=5)
header2.grid(row=0, column=1, padx=5, pady=5)

prayer_labels = {}

prayer_times = get_prayer_times()

if prayer_times:
    location_label.config(text=f"Location: {prayer_times['location']}")  
    row = 1
    for prayer, time in prayer_times["prayers"].items():
        label_prayer = tk.Label(table_frame, text=prayer, font=FONT_BODY, bg=COLOR_SURFACE, fg=COLOR_TEXT, width=15, padx=10, pady=5)
        label_prayer.grid(row=row, column=0, padx=5, pady=5)
        label_time = tk.Label(table_frame, text=time, font=FONT_BODY, bg=COLOR_SURFACE, fg=COLOR_TEXT, width=10, padx=10, pady=5)
        label_time.grid(row=row, column=1, padx=5, pady=5)
        prayer_labels[prayer] = label_time
        row += 1

# Developer Label
dev_label = tk.Label(root, text="Prepared by Md Ariful Islam", font=("Roboto", 10), bg=COLOR_BACKGROUND, fg=COLOR_TEXT_SECONDARY)
dev_label.pack(pady=20)

# Start the prayer time checking thread
threading.Thread(target=check_prayer_time, daemon=True).start()

# Start the prayer time updating thread
threading.Thread(target=update_prayer_times, daemon=True).start()

# Run the application
root.mainloop()