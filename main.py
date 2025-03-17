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
    """Načte konfiguraci z config.json, pokud neexistuje, vrátí prázdné hodnoty."""
    if not os.path.exists(CONFIG_FILE):
        return {
            "captain_name": "",
            "first_officer": "",
            "openai_api_key": ""
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 Funkce pro uložení konfigurace
def save_config(config):
    """Uloží konfiguraci do config.json."""
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

# 🛠 Kontrola API klíče
config = load_config()
if not config.get("openai_api_key"):
    root = tk.Tk()
    root.withdraw()  # Skryje hlavní okno
    api_key = simpledialog.askstring("Setup OPEN AI API", "Insert your OPEN AI API key:", show="*")
    
    if not api_key:
        messagebox.showerror("Error", "Insert OpenAI API key!")
        exit()

    config["openai_api_key"] = api_key
    save_config(config)

# ✅ Teď už můžeme importovat announcement_generator
import announcement_generator

# 🔥 Spuštění Flask serveru v samostatném vlákně
print("🚀 Spouštím Flask server...")
flask_thread = threading.Thread(target=flask_server.start_flask_server, daemon=True)
flask_thread.start()

# 🌍 Možnosti pro jazyk a styl hlasu
valid_languages = announcement_generator.valid_languages
captain_styles = announcement_generator.captain_styles
selected_languages = []

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



def set_lua_script_path():
    """Umožní uživateli vybrat složku, kde se nachází Lua skript, a uloží cestu do config.json."""
    folder_selected = filedialog.askdirectory(title="Select Lua script folder")
    
    if folder_selected:
        config = load_config()
        config["lua_script_path"] = folder_selected
        save_config(config)
        messagebox.showinfo("Saved", "Lua script path saved successfully!")
        update_flight_data_path()

# ✈ **UI pro nastavení jazyka, hlasu a osobních údajů**
def open_settings_window():
    def browse_lua_script():
        """Otevře dialog pro výběr Lua souboru nebo složky."""
        path = filedialog.askdirectory()  # Můžeme použít `askopenfilename()` pokud chceme přesný soubor
        if path:
            lua_script_path_var.set(path)

    def submit():
        global primary_lang, secondary_langs, captain_style, captain_name, first_officer, openai_api_key, lua_script_path, flight_data_file

        primary_lang = primary_lang_var.get()
        secondary_langs = [lang for lang, var in secondary_vars.items() if var.get()]
        captain_style = style_var.get()
        captain_name = captain_name_var.get().strip()
        first_officer = first_officer_var.get().strip()
        openai_api_key = api_key_var.get().strip()
        lua_script_path = lua_script_path_var.get().strip()  # ✅ Zajištěná existence
        flight_data_file = flight_data_file_var.get().strip()  # ✅ Nově přidáno

        if not captain_name or not first_officer:
            messagebox.showwarning("Error", "Insert name of captain and first officer!")
            return
        if not primary_lang:
            messagebox.showwarning("Error", "Choose primary language!")
            return
        if not captain_style:
            messagebox.showwarning("Error", "Choose voice tone!")
            return
        if not openai_api_key:
            messagebox.showwarning("Error", "Missing Open AI key!")
            return
        if not lua_script_path:
            messagebox.showwarning("Error", "Select Lua script directory!")
            return
        if not flight_data_file:
            messagebox.showwarning("Error", "Select flight data file!")
            return

        # 💾 Uložit do config.json
        save_config({
            "captain_name": captain_name,
            "first_officer": first_officer,
            "openai_api_key": openai_api_key,
            "primary_language": primary_lang,
            "secondary_languages": secondary_langs,
            "captain_style": captain_style,
            "lua_script_path": lua_script_path,
            "flight_data_file": flight_data_file
        })

        messagebox.showinfo("Saved", "All good to go!")
        settings_window.destroy()

    settings_window = tk.Tk()
    settings_window.title("Voice and language setup")
    settings_window.geometry("1200x850")  # Trochu zvětšíme okno pro novou kolonku

    frame = tk.Frame(settings_window, padx=15, pady=15)
    frame.pack(fill="both", expand=True)

    # 🔄 Načtení konfigurace
    config = load_config()

    lua_script_path_var = tk.StringVar(value=config.get("lua_script_path", ""))
    flight_data_file_var = tk.StringVar(value=config.get("flight_data_file", ""))


    # 🧑‍✈ **Jméno kapitána a FO**
    tk.Label(frame, text="Captain Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
    captain_name_var = tk.StringVar(value=config.get("captain_name", ""))
    tk.Entry(frame, textvariable=captain_name_var, font=("Arial", 11), width=30).grid(row=0, column=1, pady=5, sticky="ew")

    tk.Label(frame, text="First Officer Name:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
    first_officer_var = tk.StringVar(value=config.get("first_officer", ""))
    tk.Entry(frame, textvariable=first_officer_var, font=("Arial", 11), width=30).grid(row=1, column=1, pady=5, sticky="ew")

    # 🔑 **API Klíč pro OpenAI**
    tk.Label(frame, text="OpenAI API Key:", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
    api_key_var = tk.StringVar(value=config.get("openai_api_key", ""))
    tk.Entry(frame, textvariable=api_key_var, font=("Arial", 11), width=30, show="*").grid(row=2, column=1, pady=5, sticky="ew")

    # 📂 Flight Data File Path
    tk.Label(frame, text="Path to flight_data.txt:", font=("Arial", 11)).grid(row=4, column=0, sticky="w", pady=5)
    tk.Entry(frame, textvariable=flight_data_file_var, font=("Arial", 11), width=30).grid(row=4, column=1, pady=5, sticky="ew")
    tk.Button(frame, text="Browse", command=browse_flight_data_file, font=("Arial", 11)).grid(row=4, column=2, padx=5)
    


    # 🌍 **Primární jazyk**
    tk.Label(frame, text="Primary language (will be used for communication between crew):", font=("Arial", 11)).grid(row=2, column=0, sticky="w", pady=5)
    primary_lang_var = tk.StringVar(value="english")
    primary_lang_dropdown = ttk.Combobox(frame, textvariable=primary_lang_var, values=[
        "afrikaans", "arabic", "armenian", "azerbaijani", "belarusian", "bosnian", "bulgarian", 
        "catalan", "chinese", "croatian", "czech", "danish", "dutch", "english", "estonian", 
        "finnish", "french", "galician", "german", "greek", "hebrew", "hindi", "hungarian", 
        "icelandic", "indonesian", "italian", "japanese", "kannada", "kazakh", "korean", 
        "latvian", "lithuanian", "macedonian", "malay", "marathi", "maori", "nepali", 
        "norwegian", "persian", "polish", "portuguese", "romanian", "russian", "serbian", 
        "slovak", "slovenian", "spanish", "swahili", "swedish", "tagalog", "tamil", "thai", 
        "turkish", "ukrainian", "urdu", "vietnamese", "welsh"
    ], state="readonly", width=20)
    primary_lang_dropdown.grid(row=2, column=1, pady=5, sticky="ew")

    # 📜 **Sekundární jazyky**
    tk.Label(frame, text="Secondary language (you can select multiple):", font=("Arial", 11)).grid(row=3, column=0, sticky="w", pady=5)

    secondary_vars = {}
    lang_frame = tk.Frame(frame)
    lang_frame.grid(row=3, column=1, pady=5, sticky="ew")

    langs_per_row = 5  # 🖥 Více jazyků na řádek → lepší přizpůsobení
    lang_list = [
        "afrikaans", "arabic", "armenian", "azerbaijani", "belarusian", "bosnian", "bulgarian", 
        "catalan", "chinese", "croatian", "czech", "danish", "dutch", "english", "estonian", 
        "finnish", "french", "galician", "german", "greek", "hebrew", "hindi", "hungarian", 
        "icelandic", "indonesian", "italian", "japanese", "kannada", "kazakh", "korean", 
        "latvian", "lithuanian", "macedonian", "malay", "marathi", "maori", "nepali", 
        "norwegian", "persian", "polish", "portuguese", "romanian", "russian", "serbian", 
        "slovak", "slovenian", "spanish", "swahili", "swedish", "tagalog", "tamil", "thai", 
        "turkish", "ukrainian", "urdu", "vietnamese", "welsh"
    ]

    row, col = 0, 0
    for lang in lang_list:
        var = tk.BooleanVar()
        chk = tk.Checkbutton(lang_frame, text=lang.capitalize(), variable=var, font=("Arial", 9))
        chk.grid(row=row, column=col, sticky="w", padx=5, pady=2)
        secondary_vars[lang] = var
        col += 1
        if col >= langs_per_row:  # Po určitém počtu jazyků skočí na nový řádek
            col = 0
            row += 1

    # 🎭 **Výběr stylu hlasu kapitána**
    tk.Label(frame, text="Captain style:", font=("Arial", 11)).grid(row=4, column=0, sticky="w", pady=5)
    style_var = tk.StringVar(value="professional")

    style_frame = tk.Frame(frame)
    style_frame.grid(row=4, column=1, pady=5, sticky="ew")

    for style in ["professional", "austere", "friendly", "experienced"]:
        tk.Radiobutton(style_frame, text=style, variable=style_var, value=style.lower(), font=("Arial", 10)).pack(side="left", padx=5)

    # ✅ **Tlačítko pro potvrzení**
    submit_button = tk.Button(settings_window, text="confirm", command=submit, font=("Arial", 12))
    submit_button.pack(pady=10)

    settings_window.mainloop()

# 🔥 Spustíme UI pro výběr jazyků, hlasu a jmen
open_settings_window()

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



    print(f"🛫 Potvrzen let: {selected_flight['flight_number']} ({selected_flight['origin']} → {selected_flight['destination']})")

    last_phase = None
    played_safety_announcement = False
    safety_announcement_triggered = False

    while True:
        phase = flask_server.flight_data["phase"]

        # 🛫 **Pokud je fáze "Pushback", nejprve proběhne "Cabin crew arm doors and crosscheck"**
        if phase == "Pushback" and not safety_announcement_triggered:
            print("🛫 Pushback zahájen! Hlášení 'Cabin crew arm doors and crosscheck'...")
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
                print(f"🎬 Spouštím bezpečnostní video: {selected_safety_video}")
                announcement_generator.play_safety_announcement(aircraft, selected_safety_video, primary_lang, secondary_langs)
            elif safety_announcement_option == "generated":
                print("🎙️ Generuji a spouštím bezpečnostní hlášení...")
                announcement_generator.play_safety_announcement(aircraft, None, primary_lang, secondary_langs)
            else:
                print("⏩ Přeskakuji bezpečnostní hlášení.")


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


