import threading
import tkinter as tk
import time
import os
import json
from flask import Flask, request, jsonify, render_template, redirect, url_for
import threading
from announcement_generator import play_announcement, play_safety_announcement, find_safety_videos

CONFIG_FILE = "config.json"

# Globální proměnné pro stav letu
flight_info = None
flight_phase = None
flight_data = {
    "phase": "Unknown",
    "altitude": 0,
    "speed": 0,
    "vertical_speed": 0,
    "beacon": 0,
    "strobe": 0,
    "taxi_light": 0,
    "landing_light": 0,
    "temperature": 20.0,
    "local_time": "12:00"
}

last_logged_phase = None
last_log_time = time.time()
FLIGHT_DATA_FILE = None

# Fáze letu
FLIGHT_PHASES = [
    "AirportBoarding", "Gate", "Pushback", "Takeoff", "Climb", "Cruise",
    "Descent", "Final", "TaxiAfterLanding", "Deboarding"
]

def load_config():
    """Načte konfiguraci z config.json."""
    if not os.path.exists(CONFIG_FILE):
        return {"lua_script_path": "", "flight_data_file": ""}
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
                            elif key == "local_time":
                                # Formátování local_time na HH:MM
                                if ":" in value:
                                    value = value[:5]  # Vezmeme pouze první 5 znaků (HH:MM)
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

def run_flight():
    global flight_phase
    config = load_config()
    all_langs_sorted = list(set([config["primary_language"]] + config["secondary_languages"]))
    airport_langs = config["airport_announcement_languages"]
    airport_order = config.get("airport_announcement_order", [])
    airport_langs_sorted = [lang for lang, _ in sorted(airport_order, key=lambda x: x[1])] if airport_order else airport_langs
    captain_style = config.get("captain_style", "professional")

    for phase in FLIGHT_PHASES:
        flight_phase = phase
        if phase == "AirportBoarding":
            play_announcement(phase, flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style)
        elif phase == "Gate":
            play_announcement(phase, flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style)
            # Čekání na další akci (např. Last Call nebo Next Phase)
            while flight_phase == "Gate":
                time.sleep(1)
        elif phase == "Cruise":
            play_announcement(phase, flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style)
            # Čekání na další akci (např. Inflight Service nebo Next Phase)
            while flight_phase == "Cruise":
                time.sleep(1)
        else:
            play_announcement(phase, flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style)
        time.sleep(5)  # Simulace času mezi fázemi

app = Flask(__name__)

@app.route('/')
def index():
    safety_videos = find_safety_videos("icao_code")  # Nahradit skutečným ICAO kódem
    return render_template('index.html', flight_phase=flight_phase, flight_info=flight_info, safety_videos=safety_videos)

@app.route('/start_flight', methods=['POST'])
def start_flight():
    global flight_info, flight_phase
    flight_info = {
        "flight_number": request.form['flight_number'],
        "origin": request.form['origin'],
        "destination": request.form['destination'],
        "gate": request.form['gate'],  # Nové pole pro gate
        "aircraft": request.form['aircraft'],
        "airline": request.form['airline'],
        "duration": request.form['duration'],
        "primary_lang": "english",
        "food_options": request.form['food_options'],  # Možnosti jídla
        "beverage_service": request.form['beverage_service'],  # Typ nápojové služby
    }
    flight_phase = None
    # Spustíme let v samostatném vlákně
    threading.Thread(target=run_flight, daemon=True).start()
    return redirect(url_for('index'))

@app.route('/next_phase', methods=['POST'])
def next_phase():
    global flight_phase
    if flight_phase in FLIGHT_PHASES:
        current_index = FLIGHT_PHASES.index(flight_phase)
        if current_index < len(FLIGHT_PHASES) - 1:
            flight_phase = FLIGHT_PHASES[current_index + 1]
    return redirect(url_for('index'))

@app.route('/last_call', methods=['POST'])
def last_call():
    config = load_config()
    all_langs_sorted = list(set([config["primary_language"]] + config["secondary_languages"]))
    airport_langs = config["airport_announcement_languages"]
    airport_order = config.get("airport_announcement_order", [])
    airport_langs_sorted = [lang for lang, _ in sorted(airport_order, key=lambda x: x[1])] if airport_order else airport_langs
    captain_style = config.get("captain_style", "professional")

    if flight_phase == "Gate":
        play_announcement("LastCall", flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style)
    return redirect(url_for('index'))

@app.route('/meal_service', methods=['POST'])
def meal_service():
    config = load_config()
    all_langs_sorted = list(set([config["primary_language"]] + config["secondary_languages"]))
    airport_langs = config["airport_announcement_languages"]
    airport_order = config.get("airport_announcement_order", [])
    airport_langs_sorted = [lang for lang, _ in sorted(airport_order, key=lambda x: x[1])] if airport_order else airport_langs
    captain_style = config.get("captain_style", "professional")

    if flight_phase == "Cruise":
        play_announcement("InflightService", flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style)
    return redirect(url_for('index'))

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

    # Funkce pro spuštění Last Call
    def trigger_last_call():
        if flight_data['phase'] == "Gate":
            config = load_config()
            all_langs_sorted = list(set([config["primary_language"]] + config["secondary_languages"]))
            airport_langs = config["airport_announcement_languages"]
            airport_order = config.get("airport_announcement_order", [])
            airport_langs_sorted = [lang for lang, _ in sorted(airport_order, key=lambda x: x[1])] if airport_order else airport_langs
            captain_style = config.get("captain_style", "professional")

            # Spustíme play_announcement na samostatném vlákně
            threading.Thread(
                target=play_announcement,
                args=("LastCall", flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style),
                daemon=True
            ).start()

    # Funkce pro spuštění Inflight Service
    def trigger_meal_service():
        if flight_data['phase'] == "Cruise":
            config = load_config()
            all_langs_sorted = list(set([config["primary_language"]] + config["secondary_languages"]))
            airport_langs = config["airport_announcement_languages"]
            airport_order = config.get("airport_announcement_order", [])
            airport_langs_sorted = [lang for lang, _ in sorted(airport_order, key=lambda x: x[1])] if airport_order else airport_langs
            captain_style = config.get("captain_style", "professional")
            
            # Spustíme play_announcement na samostatném vlákně
            threading.Thread(
                target=play_announcement,
                args=("InflightService", flight_info, flight_data, all_langs_sorted, airport_langs_sorted, airport_order, captain_style),
                daemon=True
            ).start()

    # Tlačítko pro Last Call
    last_call_button = tk.Button(root, text="Last Call", font=("Arial", 12), command=trigger_last_call)
    last_call_button.pack(pady=5)

    # Tlačítko pro Inflight Service
    meal_service_button = tk.Button(root, text="Inflight Service", font=("Arial", 12), command=trigger_meal_service)
    meal_service_button.pack(pady=5)

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
        # Aktivace/deaktivace tlačítek podle fáze letu
        if flight_data['phase'] == "Gate":
            last_call_button.config(state="normal")
        else:
            last_call_button.config(state="disabled")

        if flight_data['phase'] == "Cruise":
            meal_service_button.config(state="normal")
        else:
            meal_service_button.config(state="disabled")

        root.after(1000, update_ui)

    update_ui()
    root.mainloop()

# 🏃‍♂️ Spustíme čtení souboru v samostatném vlákně
data_thread = threading.Thread(target=read_flight_data, daemon=True)
data_thread.start()

def start_flask_server():
    """Spustí Flask server."""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

# **Spustíme server ve vlákně**
if __name__ == "__main__":
    start_gui()