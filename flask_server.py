import threading
import tkinter as tk
import time
import os
import json
from flask import Flask, request, jsonify
import threading

CONFIG_FILE = "config.json"

flight_data = {
    "phase": "Unknown",
    "altitude": 0,
    "speed": 0,
    "vertical_speed": 0,
    "beacon": 0,
    "strobe": 0,
    "taxi_light": 0,
    "landing_light": 0,
    "temperature": 20.0
}

last_logged_phase = None
last_log_time = time.time()
FLIGHT_DATA_FILE = None


def load_config():
    """Načte konfiguraci z config.json."""
    if not os.path.exists(CONFIG_FILE):
        return {"lua_script_path": ""}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def update_flight_data_path():
    """Načte cestu k flight_data.txt z config.json."""
    global FLIGHT_DATA_FILE
    config = load_config()
    file_path = config.get("flight_data_file", "").strip()

    if file_path and os.path.exists(file_path):
        FLIGHT_DATA_FILE = file_path
        print(f"✅ Flight data file found: {FLIGHT_DATA_FILE}")
    else:
        print("⚠️ Flight data file is not set or invalid in config.json!")



update_flight_data_path()


def read_flight_data():
    """Čte data z flight_data.txt každou sekundu."""
    global flight_data, last_logged_phase, last_log_time

    while True:
        if FLIGHT_DATA_FILE and os.path.exists(FLIGHT_DATA_FILE):
            try:
                with open(FLIGHT_DATA_FILE, "r") as f:
                    lines = f.readlines()
                
                new_data = {}
                for line in lines:
                    line = line.strip()
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        if key in flight_data:
                            if key in ["phase"]:
                                new_data[key] = value
                            else:
                                try:
                                    new_data[key] = float(value)
                                except ValueError:
                                    print(f"⚠️ Invalid value for {key}: {value}")

                # Pokud soubor obsahuje platná data, aktualizujeme flight_data
                if new_data:
                    flight_data.update(new_data)

            except Exception as e:
                print(f"❌ Error reading flight_data.txt: {e}")

        else:
            print("⚠️ flight_data.txt file does not exist, waiting for data...")

        # 📡 Logování pouze při změně fáze nebo každých 5 sekund
        current_time = time.time()
        if flight_data["phase"] != last_logged_phase or (current_time - last_log_time) >= 5:
            print(f"📡 Flight phase updated: {flight_data['phase']} (Altitude: {flight_data['altitude']} ft, Speed: {flight_data['speed']} knots)")
            last_logged_phase = flight_data["phase"]
            last_log_time = current_time

        time.sleep(1)


def start_gui():
    """Spustí GUI pro sledování letových fází."""
    root = tk.Tk()
    root.title("Flight Phase Monitor")

    phase_label = tk.Label(root, text="Flight Phase: Unknown", font=("Arial", 14))
    phase_label.pack()
    
    altitude_label = tk.Label(root, text="Altitude: 0 ft", font=("Arial", 14))
    altitude_label.pack()

    speed_label = tk.Label(root, text="Speed: 0 knots", font=("Arial", 14))
    speed_label.pack()

    vs_label = tk.Label(root, text="Vertical Speed: 0 ft/min", font=("Arial", 14))
    vs_label.pack()

    lights_label = tk.Label(root, text="Lights: Beacon(0) Strobe(0) Taxi(0) Landing(0)", font=("Arial", 14))
    lights_label.pack()

    def update_ui():
        """Pravidelně aktualizuje data v GUI."""
        phase_label.config(text=f"Flight Phase: {flight_data['phase']}")
        altitude_label.config(text=f"Altitude: {flight_data['altitude']} ft")
        speed_label.config(text=f"Speed: {flight_data['speed']} knots")
        vs_label.config(text=f"Vertical Speed: {flight_data['vertical_speed']} ft/min")
        lights_label.config(
            text=f"Lights: Beacon({flight_data['beacon']}) Strobe({flight_data['strobe']}) "
                 f"Taxi({flight_data['taxi_light']}) Landing({flight_data['landing_light']})"
        )
        root.after(1000, update_ui)

    update_ui()
    root.mainloop()


# 🏃‍♂️ Spustíme čtení souboru v samostatném vlákně
data_thread = threading.Thread(target=read_flight_data, daemon=True)
data_thread.start()

app = Flask(__name__)

def start_flask_server():
    """Spustí Flask server."""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)



# **Spustíme server ve vlákně**
if __name__ == "__main__":
    start_gui()
