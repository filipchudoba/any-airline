import threading
import tkinter as tk
from flask import Flask, request, jsonify
import logging
import time

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)  # Skryje všechny běžné HTTP requesty


# Inicializace Flask aplikace
app = Flask(__name__)

# Globální proměnné pro letová data
flight_data = {
    "phase": "Unknown",
    "altitude": 0,
    "speed": 0,
    "vertical_speed": 0,
    "beacon": 0,
    "strobe": 0,
    "taxi_light": 0,
    "landing_light": 0
}

last_logged_phase = None  # Uloží poslední vypsanou fázi
last_log_time = time.time()  # Čas posledního logu

@app.route('/update_flight_phase', methods=['POST'])
def update_flight_phase():
    """Přijímá data z X-Plane a aktualizuje letové informace."""
    global flight_data, last_logged_phase, last_log_time
    data = request.json
    if data:
        new_phase = data.get("phase", "Unknown")
        flight_data["phase"] = new_phase
        flight_data["altitude"] = round(data.get("altitude", 0), 2)
        flight_data["speed"] = round(data.get("speed", 0), 2)
        flight_data["vertical_speed"] = round(data.get("vertical_speed", 0), 2)
        flight_data["beacon"] = data.get("beacon", 0)
        flight_data["strobe"] = data.get("strobe", 0)
        flight_data["taxi_light"] = data.get("taxi_light", 0)
        flight_data["landing_light"] = data.get("landing_light", 0)
        flight_data["temperature"] = round(data.get("temperature", 20.0), 1)

        # 🔥 Logování POUZE při změně fáze nebo každých 5 sekund
        current_time = time.time()
        if new_phase != last_logged_phase or (current_time - last_log_time) >= 5:
            print(f"📡 Přijata fáze letu: {new_phase} (Altitude: {flight_data['altitude']} ft, Speed: {flight_data['speed']} knots)")
            last_logged_phase = new_phase
            last_log_time = current_time  # Aktualizujeme čas posledního logu

        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "No data received"}), 400



def start_flask_server():
    """Spustí Flask server v samostatném vlákně."""
    app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)

def start_gui():
    """Spustí jednoduché GUI pro monitorování letových dat."""
    root = tk.Tk()
    root.title("Flight Phase Monitor")

    # Štítky pro zobrazení dat
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

# Spuštění Flask serveru na pozadí
flask_thread = threading.Thread(target=start_flask_server, daemon=True)
flask_thread.start()

# GUI může být spuštěno na vyžádání (odstranění blokování)
if __name__ == "__main__":
    start_gui()
