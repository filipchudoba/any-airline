import requests
import time
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

def fetch_departures(airport_code):
    """Načte seznam odletů z Flightradar24 API podle kódu letiště."""
    timestamp = int(time.time())
    url = f"https://api.flightradar24.com/common/v1/airport.json?code={airport_code}&plugin[]=&plugin-setting[schedule][mode]=departures&plugin-setting[schedule][timestamp]={timestamp}&page=1&limit=100"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return []
        
        data = response.json()
        if "result" not in data or "response" not in data["result"]:
            print("❌ API returned wrong data!")
            return []

        # 📌 Získání informací o letišti
        airport_data = data["result"]["response"]["airport"]["pluginData"]["details"]
        origin_name = airport_data.get("name", "Unknown")
        origin_iata = airport_data.get("code", {}).get("iata", "N/A")
        origin_icao = airport_data.get("code", {}).get("icao", "N/A")

        flights = data["result"]["response"]["airport"]["pluginData"]["schedule"]["departures"]["data"]
        departures = []

        for flight in flights:
            flight_info = flight.get("flight", {})

            flight_number = flight_info.get("identification", {}).get("number", {}).get("default", "N/A")
            airline_info = flight_info.get("airline")
            if airline_info:
                airline = airline_info.get("name", "Unknown")
                airline_icao = airline_info.get("code", {}).get("icao", "Unknown")
            else:
                airline = "Unknown"
                airline_icao = "Unknown"


            destination_info = flight_info.get("airport", {}).get("destination", {})
            destination_name = destination_info.get("name", "Unknown")
            destination_iata = destination_info.get("code", {}).get("iata", "N/A")
            destination_icao = destination_info.get("code", {}).get("icao", "N/A")

            aircraft_info = flight_info.get("aircraft", {})
            aircraft_type = aircraft_info.get("model", {}).get("text", "Unknown")

            time_info = flight_info.get("time", {}).get("scheduled", {})
            departure_time_unix = time_info.get("departure", None)
            arrival_time_unix = time_info.get("arrival", None)

            departure_time = datetime.datetime.fromtimestamp(departure_time_unix, datetime.UTC).strftime('%H:%M UTC') if departure_time_unix else "N/A"
            arrival_time = datetime.datetime.fromtimestamp(arrival_time_unix, datetime.UTC).strftime('%H:%M UTC') if arrival_time_unix else "N/A"

            if departure_time_unix and arrival_time_unix:
                duration_seconds = arrival_time_unix - departure_time_unix
                duration = f"{duration_seconds // 3600}h {duration_seconds % 3600 // 60}m"
            else:
                duration = "N/A"

            departures.append({
                "flight_number": flight_number,
                "airline": airline,
                "airline_icao": airline_icao,
                "destination": destination_name,
                "destination_iata": destination_iata,
                "destination_icao": destination_icao,
                "departure_time": departure_time,
                "origin": origin_name,
                "origin_iata": origin_iata,
                "origin_icao": origin_icao,
                "aircraft": aircraft_type,
                "duration": duration
            })

        return departures

    except requests.exceptions.RequestException as e:
        print(f"❌ Error when connecting to the API: {e}")
        return []
    except ValueError:
        print("❌ API returned empty answer!")
        return []
    except KeyError as e:
        print(f"❌ Missing key in the API request: {e}")
        return []

# 🎛 **GUI pro výběr letu**
def run_gui():
    """Spustí GUI pro výběr letu a vrátí vybraný let jako slovník."""

    def update_departures():
        """Aktualizuje tabulku odletů na základě kódu letiště."""
        airport_code = airport_code_entry.get().upper()
        departures = fetch_departures(airport_code)

        departures_table.delete(*departures_table.get_children())  

        if departures:
            for flight in departures:
                departures_table.insert("", "end", values=(
                    flight["flight_number"], flight["airline"], flight["airline_icao"],  flight["destination"],
                    flight["destination_iata"], flight["destination_icao"],
                    flight["departure_time"], flight["origin"], flight["origin_iata"], flight["origin_icao"],
                    flight["aircraft"], flight["duration"]
                ))
        else:
            departures_table.insert("", "end", values=("Žádná data", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-", "-"))

    def select_flight():
        """Uloží vybraný let a zavře okno."""
        selected_item = departures_table.selection()
        if not selected_item:
            messagebox.showwarning("Chyba", "Nejprve vyberte let!")
            return

        flight_data = departures_table.item(selected_item)["values"]
        selected_flight = {
            "flight_number": flight_data[0],
            "airline": flight_data[1],
            "airline_icao": flight_data[2],
            "destination": flight_data[3],
            "destination_iata": flight_data[4],
            "destination_icao": flight_data[5],
            "departure_time": flight_data[6],
            "origin": flight_data[7],
            "origin_iata": flight_data[8],
            "origin_icao": flight_data[9],
            "aircraft": flight_data[10],  
            "duration": flight_data[11]
        }

        root.selected_flight = selected_flight
        root.destroy()

    root = tk.Tk()
    root.title("Flight Departures Tracker")
    root.selected_flight = None

    tk.Label(root, text="IATA code of origin:", font=("Arial", 12)).pack(pady=5)
    airport_code_entry = tk.Entry(root, font=("Arial", 12))
    airport_code_entry.pack(pady=5)

    fetch_button = tk.Button(root, text="Show departures", command=update_departures, font=("Arial", 12))
    fetch_button.pack(pady=5)

    columns = ("Flight Number", "Airline", "ICAO", "Destination", "IATA", "ICAO", "Time of departure", "Origin", "Origin IATA", "Origin ICAO", "Aircraft", "Duration")
    global departures_table
    departures_table = ttk.Treeview(root, columns=columns, show="headings")

    for col in columns:
        departures_table.heading(col, text=col)
        departures_table.column(col, width=120)

    departures_table.pack(pady=10)

    select_button = tk.Button(root, text="Choose flight", command=select_flight, font=("Arial", 12))
    select_button.pack(pady=5)

    root.mainloop()
    return root.selected_flight