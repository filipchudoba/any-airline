import requests
import time
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

def fetch_departures(airport_code):
    """Načte seznam odletů z Flightradar24 API podle kódu letiště."""
    timestamp = int(time.time())
    url = f"https://api.flightradar24.com/common/v1/airport.json?code={airport_code}&plugin[]=&plugin-setting[schedule][mode]=departures&plugin-setting[schedule][timestamp]={timestamp}&page=1&limit=100"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error: {response.status_code}")
            return []
        
        data = response.json()
        if "result" not in data or "response" not in data["result"]:
            print("❌ API returned wrong data!")
            return []

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
            airline = airline_info.get("name", "Unknown") if airline_info else "Unknown"
            airline_icao = airline_info.get("code", {}).get("icao", "Unknown") if airline_info else "Unknown"

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

def add_manual_flight(root):
    """Otevře nové okno pro manuální zadání letu."""
    manual_window = tk.Toplevel(root)
    manual_window.title("Manuální zadání letu")

    fields = ["flight_number", "airline", "airline_icao", "destination", "destination_iata", "destination_icao",
              "departure_time", "origin", "origin_iata", "origin_icao", "aircraft", "duration"]
    entries = {}

    for field in fields:
        tk.Label(manual_window, text=field.replace("_", " ").capitalize()).pack()
        entry = tk.Entry(manual_window)
        entry.pack()
        entries[field] = entry

    def save_manual_flight():
        manual_flight = {field: entry.get() for field, entry in entries.items()}
        root.selected_flight = manual_flight
        manual_window.destroy()
        root.destroy()
    
    tk.Button(manual_window, text="Save the flight", command=save_manual_flight).pack()

def run_gui():
    """Spustí GUI pro výběr letu a vrátí vybraný let jako slovník."""

    def update_departures():
        """Aktualizuje tabulku odletů na základě kódu letiště."""
        airport_code = airport_code_entry.get().upper()
        departures = fetch_departures(airport_code)
        departures_table.delete(*departures_table.get_children())  
        
        if departures:
            for flight in departures:
                departures_table.insert("", "end", values=tuple(flight.values()))
        else:
            departures_table.insert("", "end", values=("Žádná data",) * 12)

    def select_flight():
        """Uloží vybraný let a zavře okno."""
        selected_item = departures_table.selection()
        if not selected_item:
            messagebox.showwarning("Chyba", "Flight is not selected. Choose one or enter your own!")
            return
        flight_data = departures_table.item(selected_item)["values"]
        root.selected_flight = dict(zip(
            ["flight_number", "airline", "airline_icao", "destination", "destination_iata", "destination_icao",
             "departure_time", "origin", "origin_iata", "origin_icao", "aircraft", "duration"],
            flight_data
        ))
        root.destroy()
    
    root = tk.Tk()
    root.title("Flight Tracker")
    root.selected_flight = None
    
    tk.Label(root, text="IATA code of origin:").pack()
    airport_code_entry = tk.Entry(root)
    airport_code_entry.pack()
    tk.Button(root, text="Show departures", command=update_departures).pack()
    tk.Button(root, text="Custom flight", command=lambda: add_manual_flight(root)).pack()
    
    columns = ["Flight Number", "Airline", "ICAO", "Destination", "IATA", "ICAO", "Time", "Origin", "IATA", "ICAO", "Aircraft", "Duration"]
    departures_table = ttk.Treeview(root, columns=columns, show="headings")
    for col in columns:
        departures_table.heading(col, text=col)
        departures_table.column(col, width=100)
    departures_table.pack()
    
    tk.Button(root, text="Choose flight", command=select_flight).pack()
    root.mainloop()
    return root.selected_flight

