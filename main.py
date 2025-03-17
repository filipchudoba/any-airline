import threading
import time
import flight_selection
import flask_server
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
from tkinter import simpledialog, messagebox
import json
import os
from tkinter import filedialog


CONFIG_FILE = "config.json"

# 🔄 Funkce pro načtení konfigurace
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "captain_name": "",
            "first_officer": "",
            "openai_api_key": "",
            "announcement_generator": "free",
            "primary_language": "english",
            "secondary_languages": [],
            "captain_style": "professional",
            "flight_data_file": ""
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 Uložení konfigurace
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 🔥 Spuštění Flask serveru v samostatném vlákně
print("🚀 Running Flask server...")
flask_thread = threading.Thread(target=flask_server.start_flask_server, daemon=True)
flask_thread.start()

def browse_flight_data_file():
    """Otevře dialog pro výběr flight_data.txt a uloží cestu do config.json."""
    file_path = filedialog.askopenfilename(title="Select flight_data.txt", filetypes=[("Text files", "*.txt")])
    
    if file_path:
        config = load_config()
        config["flight_data_file"] = file_path  # Uložíme cestu do JSON
        save_config(config)

        # ✅ Aktualizujeme proměnnou v GUI, pokud existuje
        if 'flight_data_file_var' in globals():
            flight_data_file_var.set(file_path)

        messagebox.showinfo("Saved", "Flight data file path saved successfully!")

        # ✅ Okamžitě aktualizujeme cestu v běžícím flask_server
        flask_server.update_flight_data_path()

def open_settings_window():
    def browse_flight_data_file():
        file_path = filedialog.askopenfilename(title="Select flight_data.txt", filetypes=[("Text files", "*.txt")])
        if file_path:
            flight_data_file_var.set(file_path)

    settings_window = tk.Tk()
    settings_window.title("Voice and Language Setup")
    settings_window.geometry("900x700")

    frame = tk.Frame(settings_window, padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    # 🔄 **Načtení konfigurace**
    config = load_config()

    # 🧑‍✈ **Vytvoření proměnných**
    captain_name_var = tk.StringVar(value=config.get("captain_name", ""))
    first_officer_var = tk.StringVar(value=config.get("first_officer", ""))
    api_key_var = tk.StringVar(value=config.get("openai_api_key", ""))
    primary_lang_var = tk.StringVar(value=config.get("primary_language", "english"))
    flight_data_file_var = tk.StringVar(value=config.get("flight_data_file", ""))
    generator_var = tk.StringVar(value=config.get("announcement_generator", "openai"))
    style_var = tk.StringVar(value=config.get("captain_style", "professional"))

    # 🔄 **Seznam jazyků**
    language_list = [
        "afrikaans", "arabic", "armenian", "azerbaijani", "belarusian", "bosnian", "bulgarian",
        "catalan", "chinese", "croatian", "czech", "danish", "dutch", "english", "estonian",
        "finnish", "french", "galician", "german", "greek", "hebrew", "hindi", "hungarian",
        "icelandic", "indonesian", "italian", "japanese", "kannada", "kazakh", "korean",
        "latvian", "lithuanian", "macedonian", "malay", "marathi", "maori", "nepali",
        "norwegian", "persian", "polish", "portuguese", "romanian", "russian", "serbian",
        "slovak", "slovenian", "spanish", "swahili", "swedish", "tagalog", "tamil", "thai",
        "turkish", "ukrainian", "urdu", "vietnamese", "welsh"
    ]

    # 🌍 **Inicializace sekundárních jazyků**
    secondary_vars = {}
    for lang in language_list:
        var = tk.BooleanVar(value=lang in config.get("secondary_languages", []))
        secondary_vars[lang] = var

    def submit():
        primary_lang = primary_lang_var.get()
        secondary_langs = [lang for lang, var in secondary_vars.items() if var.get()]
        captain_style = style_var.get()
        captain_name = captain_name_var.get().strip()
        first_officer = first_officer_var.get().strip()
        openai_api_key = api_key_var.get().strip() if generator_var.get() == "openai" else ""
        flight_data_file = flight_data_file_var.get().strip()
        generator = generator_var.get().strip()

        if not captain_name or not first_officer:
            messagebox.showwarning("Error", "Insert name of captain and first officer!")
            return
        if not primary_lang:
            messagebox.showwarning("Error", "Choose primary language!")
            return
        if not captain_style:
            messagebox.showwarning("Error", "Choose voice tone!")
            return
        if generator == "openai" and not openai_api_key:
            messagebox.showwarning("Error", "Missing OpenAI API key! Please enter a valid key.")
            return
        if not flight_data_file:
            messagebox.showwarning("Error", "Select flight data file!")
            return

        save_config({
            "captain_name": captain_name,
            "first_officer": first_officer,
            "openai_api_key": openai_api_key,
            "primary_language": primary_lang,
            "secondary_languages": secondary_langs,
            "captain_style": captain_style,
            "flight_data_file": flight_data_file,
            "announcement_generator": generator
        })

        messagebox.showinfo("Saved", "All good to go!")
        settings_window.destroy()

    def toggle_api_key():
        api_key_entry.config(state="normal" if generator_var.get() == "openai" else "disabled")

    # 🏷 **Captain & First Officer Name**
    tk.Label(frame, text="Captain Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
    tk.Entry(frame, textvariable=captain_name_var, font=("Arial", 11), width=30).grid(row=0, column=1, pady=5, sticky="ew")

    tk.Label(frame, text="First Officer Name:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
    tk.Entry(frame, textvariable=first_officer_var, font=("Arial", 11), width=30).grid(row=1, column=1, pady=5, sticky="ew")

    # 🗣 **Výběr hlasového generátoru**
    tk.Label(frame, text="Voice Generator:", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
    gen_frame = tk.Frame(frame)
    gen_frame.grid(row=2, column=1, pady=5, sticky="w")

    tk.Radiobutton(gen_frame, text="OpenAI (Better quality, requires API key)", variable=generator_var, value="openai", font=("Arial", 10), command=toggle_api_key).pack(anchor="w")
    tk.Radiobutton(gen_frame, text="Free (Offline, lower quality)", variable=generator_var, value="free", font=("Arial", 10), command=toggle_api_key).pack(anchor="w")

    # 🔑 **API Klíč**
    tk.Label(frame, text="OpenAI API Key:", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=5)
    api_key_entry = tk.Entry(frame, textvariable=api_key_var, font=("Arial", 11), width=30, show="*")
    api_key_entry.grid(row=3, column=1, pady=5, sticky="ew")

    toggle_api_key()

    # 📜 **Primární jazyk**
    tk.Label(frame, text="Primary language:", font=("Arial", 11)).grid(row=4, column=0, sticky="w", pady=5)
    ttk.Combobox(frame, textvariable=primary_lang_var, values=language_list, state="readonly", width=20).grid(row=4, column=1, pady=5, sticky="ew")

    # 🌍 **Sekundární jazyky**
    tk.Label(frame, text="Secondary languages:", font=("Arial", 11)).grid(row=5, column=0, sticky="w", pady=5)
    lang_frame = tk.Frame(frame)
    lang_frame.grid(row=5, column=1, pady=5, sticky="ew")

    for i, lang in enumerate(language_list):
        tk.Checkbutton(lang_frame, text=lang.capitalize(), variable=secondary_vars[lang], font=("Arial", 9)).grid(row=i // 5, column=i % 5, sticky="w")

    # 🎭 **Tón hlasu kapitána**
    tk.Label(frame, text="Captain Style:", font=("Arial", 11)).grid(row=6, column=0, sticky="w", pady=5)
    ttk.Combobox(frame, textvariable=style_var, values=["professional", "austere", "friendly", "experienced"], state="readonly", width=20).grid(row=6, column=1, pady=5, sticky="ew")

    # 📂 **Výběr flight_data.txt**
    tk.Button(frame, text="Browse flight_data.txt", command=browse_flight_data_file).grid(row=7, column=0, columnspan=2, pady=5)

    # ✅ **Potvrzovací tlačítko**
    tk.Button(settings_window, text="Confirm", command=submit, font=("Arial", 12)).pack(pady=10)

    settings_window.mainloop()

# Otevře okno pro nastavení a uloží konfiguraci
open_settings_window()


# ✅ Načteme novou konfiguraci po zavření okna
config = load_config()

# 💾 Proměnné se správně načtou z konfigurace
captain_name = config["captain_name"]
first_officer = config["first_officer"]
openai_api_key = config["openai_api_key"]
primary_lang = config["primary_language"]
secondary_langs = config["secondary_languages"]
captain_style = config["captain_style"]
flight_data_file = config["flight_data_file"]
generator = config["announcement_generator"]

import announcement_generator
# 🌍 Možnosti pro jazyk a styl hlasu
valid_languages = announcement_generator.valid_languages
captain_styles = announcement_generator.captain_styles
selected_languages = []

# 🛫 GUI pro potvrzení letu
selected_flight = flight_selection.run_gui()

if selected_flight:
    # ✅ **Bezpečné získání ICAO kódu aerolinky**
    airline_icao = selected_flight.get("airline_icao") or selected_flight.get("icao") or "Unknown"

    # ✅ **Vyhledání bezpečnostních videí**
    safety_videos = announcement_generator.find_safety_videos(airline_icao)

    def confirm_flight():
        global aircraft, airline, flight_duration, safety_announcement_option, selected_safety_video
        aircraft = aircraft_var.get().strip()
        airline = airline_var.get().strip()
        flight_duration = flight_duration_var.get().strip()
        safety_announcement_option = safety_var.get()  # ✅ Uložíme výběr bezpečnostního hlášení
        selected_safety_video = video_var.get()  # ✅ Uložíme vybraný soubor

        if not aircraft or not airline or not flight_duration:
            messagebox.showwarning("Error", "All fields must be filled out!")
            return
        
        flight_window.destroy()
        flight_confirmed.set(True)

    # 📌 Vytvoření okna
    flight_window = tk.Tk()
    flight_window.title("Confirm")

    # ✈ **Letadlo**
    tk.Label(flight_window, text="Aircraft:", font=("Arial", 12)).pack(pady=5)
    aircraft_var = tk.StringVar(value=selected_flight.get("aircraft", "Boeing 737"))
    tk.Entry(flight_window, textvariable=aircraft_var, font=("Arial", 12), width=30).pack(pady=5)

    # 🏢 **Aerolinka**
    tk.Label(flight_window, text="Airline:", font=("Arial", 12)).pack(pady=5)
    airline_var = tk.StringVar(value=selected_flight.get("airline", "Unknown"))
    tk.Entry(flight_window, textvariable=airline_var, font=("Arial", 12), width=30).pack(pady=5)

    # ⏳ **Doba letu**
    tk.Label(flight_window, text="Duration (ex. 2h 15m):", font=("Arial", 12)).pack(pady=5)
    flight_duration_var = tk.StringVar(value=selected_flight.get("duration", "2h 15m"))
    tk.Entry(flight_window, textvariable=flight_duration_var, font=("Arial", 12), width=30).pack(pady=5)

    # 📢 **Bezpečnostní hlášení - výběr**
    tk.Label(flight_window, text="Safety announcement:", font=("Arial", 12, "bold")).pack(pady=10)

    safety_var = tk.StringVar(value="video")  # Výchozí možnost = Použít video

    tk.Radiobutton(flight_window, text="📼 Use safety video (if exists)", 
                   variable=safety_var, value="video", font=("Arial", 11)).pack(anchor="w")

    tk.Radiobutton(flight_window, text="🎙 Generate safety announcement", 
                   variable=safety_var, value="generated", font=("Arial", 11)).pack(anchor="w")

    tk.Radiobutton(flight_window, text="⏩ Skip", 
                   variable=safety_var, value="skip", font=("Arial", 11)).pack(anchor="w")

    # ✅ **Pokud existují bezpečnostní videa, nabídneme je k výběru**
    tk.Label(flight_window, text="Choose safety video:", font=("Arial", 12, "bold")).pack(pady=5)
    video_var = tk.StringVar(value=safety_videos[0] if safety_videos else "")

    if safety_videos:
        for video in safety_videos:
            tk.Radiobutton(flight_window, text=os.path.basename(video), variable=video_var, value=video).pack(anchor="w")
    else:
        tk.Label(flight_window, text="❌ No videos available!", fg="red", font=("Arial", 11)).pack()

    # ✅ **Potvrzení**
    submit_button = tk.Button(flight_window, text="Confirm", command=confirm_flight, font=("Arial", 12))
    submit_button.pack(pady=10)

    flight_confirmed = tk.BooleanVar(value=False)
    flight_window.mainloop()

    if not flight_confirmed.get():
        exit()

    print(f"🛫 Confirmed flight: {selected_flight['flight_number']} ({selected_flight['origin']} → {selected_flight['destination']})")

    # 🔥 Spuštění GUI Flight Phase Monitor v samostatném vlákně
    print("🖥 Spouštím GUI Flight Phase Monitor...")
    gui_thread = threading.Thread(target=flask_server.start_gui, daemon=True)
    gui_thread.start()

    # 👀 **Funkce pro sledování GUI**
    def monitor_gui():
        """Sleduje, zda GUI běží, a pokud se ukončí, vypne celý program."""
        while True:
            if not gui_thread.is_alive():
                print("❌ GUI Flight Phase Monitor closed! Ending the script...")
                os._exit(1)  # Tvrdé ukončení programu
            time.sleep(1)  # ✅ Každou sekundu kontroluje stav GUI

    # 🚀 **Spustíme monitorovací vlákno**
    monitor_thread = threading.Thread(target=monitor_gui, daemon=True)
    monitor_thread.start()

    # 🔥 **Kód pokračuje dál, nic se nezastaví!**
    print("✅ GUI is running on background!")

    last_phase = None
    played_safety_announcement = False
    safety_announcement_triggered = False

    while True:
        phase = flask_server.flight_data["phase"]

        # 🛫 **Pokud je fáze "Pushback", nejprve proběhne "Cabin crew arm doors and crosscheck"**
        if phase == "Pushback" and not safety_announcement_triggered:
            print("🛫 Pushback started! Arm doors and crosscheck")
            announcement_generator.play_announcement(
                "Pushback",
                {
                    "captain_name": captain_name,
                    "first_officer": first_officer,
                    "flight_number": selected_flight["flight_number"],
                    "origin": selected_flight["origin"],
                    "destination": selected_flight["destination"],
                    "aircraft": aircraft,
                    "airline": airline,
                    "duration": flight_duration
                },
                flask_server.flight_data,
                primary_lang,
                secondary_langs,
                captain_style
            )
            time.sleep(5)  # ⏳ Počkáme 10 sekund

            # 📢 **Po 10 sekundách spustíme bezpečnostní video nebo hlášení**
            if safety_announcement_option == "video" and os.path.exists(selected_safety_video):
                print(f"🎬 Playing safety video: {selected_safety_video}")
                announcement_generator.play_safety_announcement(aircraft, selected_safety_video, primary_lang, secondary_langs)
            elif safety_announcement_option == "generated":
                print("🎙️ Generating safety demo...")
                announcement_generator.play_safety_announcement(aircraft, None, primary_lang, secondary_langs)
            else:
                print("⏩ Skipping safety demo.")


            played_safety_announcement = True
            safety_announcement_triggered = True

        # 🗣️ **Ostatní normální letová hlášení**
        if phase != last_phase and phase in announcement_generator.ANNOUNCEMENTS:
            announcement_generator.play_announcement(
                phase,
                {
                    "captain_name": captain_name,
                    "first_officer": first_officer,
                    "flight_number": selected_flight["flight_number"],
                    "origin": selected_flight["origin"],
                    "destination": selected_flight["destination"],
                    "aircraft": aircraft,
                    "airline": airline,
                    "duration": flight_duration
                },
                flask_server.flight_data,
                primary_lang,
                secondary_langs,
                captain_style
            )

            last_phase = phase

        time.sleep(5)

