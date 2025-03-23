print("Please wait, program is starting...")
import threading
print("10%")
import time
print("20%")
import flight_selection
print("30%")
import tkinter as tk
print("40%")
from tkinter import ttk, messagebox, filedialog
print("50%")
import json
print("60%")
import os
print("70%")
import pygame
print("80%")
from pydub import AudioSegment
print("90%")
print("100%")
import sys

BASE_DIR = os.path.dirname(sys.executable) if getattr(sys, 'frozen', False) else os.path.dirname(__file__)
CONFIG_FILE = "config.json"

# Dočasná proměnná pro uložení cesty k flight_data.txt
pending_flight_data_path = None

# 🔄 Function to load configuration
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {
            "captain_name": "",
            "first_officer": "",
            "openai_api_key": "",
            "announcement_generator": "free",
            "primary_language": "english",
            "secondary_languages": [],
            "airport_announcement_languages": [],
            "captain_style": "professional",
            "flight_data_file": "",
            "chime_start": "none",
            "chime_end": "none",
            "enable_airport_announcement": True
        }
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# 💾 Save configuration
def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)

def browse_flight_data_file():
    """Opens a dialog to select flight_data.txt and saves the path to config.json."""
    global pending_flight_data_path
    file_path = filedialog.askopenfilename(title="Select flight_data.txt", filetypes=[("Text files", "*.txt")])
    if file_path:
        config = load_config()
        config["flight_data_file"] = file_path
        save_config(config)
        if 'flight_data_file_var' in globals():
            flight_data_file_var.set(file_path)
        messagebox.showinfo("Saved", "Flight data file path saved successfully!")
        # Uložíme cestu do dočasné proměnné, aktualizace se provede později
        pending_flight_data_path = file_path

def open_language_order_window(parent, all_langs, airport_langs):
    """Otevře okno pro nastavení pořadí jazyků."""
    order_window = tk.Toplevel(parent)
    order_window.title("Set Language Order")
    order_window.geometry("600x800")

    # Proměnné pro uložení pořadí
    all_langs_order = all_langs.copy()
    airport_langs_order = airport_langs.copy()

    # Hlavní frame
    main_frame = tk.Frame(order_window, padx=10, pady=10)
    main_frame.pack(fill="both", expand=True)

    # Sekce pro In-flight languages
    inflight_frame = tk.LabelFrame(main_frame, text="In-flight Language Order", font=("Arial", 12, "bold"), padx=10, pady=10)
    inflight_frame.pack(fill="both", expand=True, pady=5)

    inflight_listbox = tk.Listbox(inflight_frame, font=("Arial", 11), height=10)
    for lang in all_langs_order:
        inflight_listbox.insert(tk.END, lang.capitalize())
    inflight_listbox.pack(fill="both", expand=True, pady=5)

    # Tlačítka pro přesun nahoru/dolů (In-flight)
    def move_up_inflight():
        selected_idx = inflight_listbox.curselection()
        if not selected_idx:
            return
        idx = selected_idx[0]
        if idx > 0:
            lang = all_langs_order.pop(idx)
            all_langs_order.insert(idx - 1, lang)
            inflight_listbox.delete(0, tk.END)
            for lang in all_langs_order:
                inflight_listbox.insert(tk.END, lang.capitalize())
            inflight_listbox.selection_set(idx - 1)

    def move_down_inflight():
        selected_idx = inflight_listbox.curselection()
        if not selected_idx:
            return
        idx = selected_idx[0]
        if idx < len(all_langs_order) - 1:
            lang = all_langs_order.pop(idx)
            all_langs_order.insert(idx + 1, lang)
            inflight_listbox.delete(0, tk.END)
            for lang in all_langs_order:
                inflight_listbox.insert(tk.END, lang.capitalize())
            inflight_listbox.selection_set(idx + 1)

    tk.Button(inflight_frame, text="Up", command=move_up_inflight, font=("Arial", 10)).pack(side="left", padx=5)
    tk.Button(inflight_frame, text="Down", command=move_down_inflight, font=("Arial", 10)).pack(side="left", padx=5)

    # Sekce pro Airport languages
    airport_frame = tk.LabelFrame(main_frame, text="Airport Language Order", font=("Arial", 12, "bold"), padx=10, pady=10)
    airport_frame.pack(fill="both", expand=True, pady=5)

    airport_listbox = tk.Listbox(airport_frame, font=("Arial", 11), height=10)
    for lang in airport_langs_order:
        airport_listbox.insert(tk.END, lang.capitalize())
    airport_listbox.pack(fill="both", expand=True, pady=5)

    # Tlačítka pro přesun nahoru/dolů (Airport)
    def move_up_airport():
        selected_idx = airport_listbox.curselection()
        if not selected_idx:
            return
        idx = selected_idx[0]
        if idx > 0:
            lang = airport_langs_order.pop(idx)
            airport_langs_order.insert(idx - 1, lang)
            airport_listbox.delete(0, tk.END)
            for lang in airport_langs_order:
                airport_listbox.insert(tk.END, lang.capitalize())
            airport_listbox.selection_set(idx - 1)

    def move_down_airport():
        selected_idx = airport_listbox.curselection()
        if not selected_idx:
            return
        idx = selected_idx[0]
        if idx < len(airport_langs_order) - 1:
            lang = airport_langs_order.pop(idx)
            airport_langs_order.insert(idx + 1, lang)
            airport_listbox.delete(0, tk.END)
            for lang in airport_langs_order:
                airport_listbox.insert(tk.END, lang.capitalize())
            airport_listbox.selection_set(idx + 1)

    tk.Button(airport_frame, text="Up", command=move_up_airport, font=("Arial", 10)).pack(side="left", padx=5)
    tk.Button(airport_frame, text="Down", command=move_down_airport, font=("Arial", 10)).pack(side="left", padx=5)

    # Potvrzení a uložení pořadí
    result = {"all_langs_order": None, "airport_langs_order": None, "confirmed": False}

    def confirm_order():
        result["all_langs_order"] = [(lang, idx + 1) for idx, lang in enumerate(all_langs_order)]
        result["airport_langs_order"] = [(lang, idx + 1) for idx, lang in enumerate(airport_langs_order)]
        result["confirmed"] = True
        order_window.destroy()

    tk.Button(order_window, text="Confirm", command=confirm_order, font=("Arial", 12), bg="#4CAF50", fg="white").pack(pady=10)

    order_window.grab_set()
    parent.wait_window(order_window)
    return result

def open_settings_window():
    settings_window = tk.Tk()
    settings_window.title("Voice and Language Setup")
    settings_window.geometry("1200x1080")

    main_frame = tk.Frame(settings_window, padx=15, pady=15)
    main_frame.pack(fill="both", expand=True)

    config = load_config()

    captain_name_var = tk.StringVar(value=config.get("captain_name", ""))
    first_officer_var = tk.StringVar(value=config.get("first_officer", ""))
    api_key_var = tk.StringVar(value=config.get("openai_api_key", ""))
    primary_lang_var = tk.StringVar(value=config.get("primary_language", "english"))
    flight_data_file_var = tk.StringVar(value=config.get("flight_data_file", ""))
    generator_var = tk.StringVar(value=config.get("announcement_generator", "openai"))
    style_var = tk.StringVar(value=config.get("captain_style", "professional"))
    airport_announcement_var = tk.BooleanVar(value=config.get("enable_airport_announcement", True))
    chime_start_var = tk.StringVar(value=config.get("chime_start", "none"))
    chime_end_var = tk.StringVar(value=config.get("chime_end", "none"))

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

    # Load list of chimes
    chime_dir = os.path.join(BASE_DIR, "airport_chimes")
    chime_files = ["none"] + [f for f in os.listdir(chime_dir) if f.endswith((".mp3", ".wav"))] if os.path.exists(chime_dir) else ["none"]

    # Secondary languages (including primary for ordering)
    secondary_vars = {}
    for lang in language_list:
        var = tk.BooleanVar(value=lang in config.get("secondary_languages", []) or lang == config.get("primary_language", "english"))
        secondary_vars[lang] = var

    # Airport languages
    airport_vars = {}
    for lang in language_list:
        var = tk.BooleanVar(value=lang in config.get("airport_announcement_languages", []))
        airport_vars[lang] = var

    # Function to play chime with validation
    def play_chime(chime_file):
        if chime_file == "none":
            return
        chime_path = os.path.join(chime_dir, chime_file)
        if not os.path.exists(chime_path):
            messagebox.showwarning("Error", f"Chime file {chime_file} not found!")
            return
        try:
            pygame.mixer.init()
            pygame.mixer.music.load(chime_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
        except Exception as e:
            messagebox.showwarning("Error", f"Failed to play chime: {str(e)}\nMake sure ffmpeg is installed!")

    def submit():
        primary_lang = primary_lang_var.get()
        all_langs = [lang for lang, var in secondary_vars.items() if var.get()]
        if primary_lang not in all_langs:
            all_langs.append(primary_lang)

        airport_langs = [lang for lang, var in airport_vars.items() if var.get()]

        captain_style = style_var.get()
        captain_name = captain_name_var.get().strip()
        first_officer = first_officer_var.get().strip()
        openai_api_key = api_key_var.get().strip() if generator_var.get() == "openai" else ""
        flight_data_file = flight_data_file_var.get().strip()
        generator = generator_var.get().strip()
        enable_airport = airport_announcement_var.get()
        chime_start = chime_start_var.get()
        chime_end = chime_end_var.get()

        if not captain_name or not first_officer or not primary_lang or not captain_style or (generator == "openai" and not openai_api_key) or not flight_data_file:
            messagebox.showwarning("Error", "All required fields must be filled!")
            return

        # Otevření okna pro nastavení pořadí jazyků
        order_result = open_language_order_window(settings_window, all_langs, airport_langs)
        if not order_result["confirmed"]:
            return  # Uživatel zrušil nastavení pořadí

        all_langs_order = order_result["all_langs_order"]
        airport_langs_order = order_result["airport_langs_order"]

        save_config({
            "captain_name": captain_name,
            "first_officer": first_officer,
            "openai_api_key": openai_api_key,
            "primary_language": primary_lang,
            "secondary_languages": [lang for lang in all_langs if lang != primary_lang],
            "all_language_order": all_langs_order,
            "airport_announcement_languages": airport_langs,
            "airport_announcement_order": airport_langs_order,
            "captain_style": captain_style,
            "flight_data_file": flight_data_file,
            "announcement_generator": generator,
            "enable_airport_announcement": enable_airport,
            "chime_start": chime_start,
            "chime_end": chime_end
        })

        messagebox.showinfo("Saved", "All good to go!")
        settings_window.destroy()

    def toggle_api_key():
        api_key_entry.config(state="normal" if generator_var.get() == "openai" else "disabled")

    # Main layout - two columns
    left_frame = tk.Frame(main_frame)
    left_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nsew")
    right_frame = tk.Frame(main_frame)
    right_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nsew")
    bottom_frame = tk.Frame(main_frame)
    bottom_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky="ew")

    # Left column - Crew and In-flight settings
    crew_frame = tk.LabelFrame(left_frame, text="Crew Information", font=("Arial", 12, "bold"), padx=10, pady=10)
    crew_frame.pack(fill="x", pady=5)

    tk.Label(crew_frame, text="Captain Name:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
    tk.Entry(crew_frame, textvariable=captain_name_var, font=("Arial", 11), width=30).grid(row=0, column=1, pady=5, sticky="ew")

    tk.Label(crew_frame, text="First Officer Name:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
    tk.Entry(crew_frame, textvariable=first_officer_var, font=("Arial", 11), width=30).grid(row=1, column=1, pady=5, sticky="ew")

    # Voice Generator
    voice_frame = tk.LabelFrame(left_frame, text="Voice Generator Settings", font=("Arial", 12, "bold"), padx=10, pady=10)
    voice_frame.pack(fill="x", pady=5)

    tk.Label(voice_frame, text="Voice Generator:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
    gen_frame = tk.Frame(voice_frame)
    gen_frame.grid(row=0, column=1, pady=5, sticky="w")
    tk.Radiobutton(gen_frame, text="OpenAI (Better quality, requires API key)", variable=generator_var, value="openai", font=("Arial", 10), command=toggle_api_key).pack(anchor="w")
    tk.Radiobutton(gen_frame, text="Free (Offline, lower quality)", variable=generator_var, value="free", font=("Arial", 10), command=toggle_api_key).pack(anchor="w")

    tk.Label(voice_frame, text="OpenAI API Key:", font=("Arial", 11)).grid(row=1, column=0, sticky="w", pady=5)
    api_key_entry = tk.Entry(voice_frame, textvariable=api_key_var, font=("Arial", 11), width=30, show="*")
    api_key_entry.grid(row=1, column=1, pady=5, sticky="ew")
    toggle_api_key()

    # In-flight languages
    inflight_frame = tk.LabelFrame(left_frame, text="In-flight Announcement Settings", font=("Arial", 12, "bold"), padx=10, pady=10)
    inflight_frame.pack(fill="both", expand=True, pady=5)

    tk.Label(inflight_frame, text="Primary language:", font=("Arial", 11)).pack(anchor="w", pady=5)
    ttk.Combobox(inflight_frame, textvariable=primary_lang_var, values=language_list, state="readonly", width=20).pack(anchor="w", pady=5)

    tk.Label(inflight_frame, text="Languages (in-flight):", font=("Arial", 11)).pack(anchor="w", pady=5)
    all_lang_frame = tk.Frame(inflight_frame, bg="#f0f0f0")
    all_lang_frame.pack(fill="x", pady=5)
    for i, lang in enumerate(language_list):
        tk.Checkbutton(all_lang_frame, text=lang.capitalize(), variable=secondary_vars[lang], font=("Arial", 9), bg="#f0f0f0").grid(row=i // 5, column=i % 5, sticky="w", padx=5)

    # Right column - Airport settings
    airport_frame = tk.LabelFrame(right_frame, text="Airport Announcement Settings", font=("Arial", 12, "bold"), padx=10, pady=10)
    airport_frame.pack(fill="both", expand=True, pady=5)

    tk.Label(airport_frame, text="Airport announcement languages:", font=("Arial", 11)).pack(anchor="w", pady=5)
    airport_lang_frame = tk.Frame(airport_frame, bg="#f0f0f0")
    airport_lang_frame.pack(fill="x", pady=5)
    for i, lang in enumerate(language_list):
        tk.Checkbutton(airport_lang_frame, text=lang.capitalize(), variable=airport_vars[lang], font=("Arial", 9), bg="#f0f0f0").grid(row=i // 5, column=i % 5, sticky="w", padx=5)

    tk.Label(airport_frame, text="Enable airport announcements:", font=("Arial", 11)).pack(anchor="w", pady=5)
    tk.Checkbutton(airport_frame, variable=airport_announcement_var, font=("Arial", 9)).pack(anchor="w")

    # Chime section
    chime_frame = tk.LabelFrame(airport_frame, text="Airport Chime Settings", font=("Arial", 11, "bold"), padx=10, pady=10)
    chime_frame.pack(fill="x", pady=10)

    tk.Label(chime_frame, text="Chime at start:", font=("Arial", 10)).pack(anchor="w", pady=2)
    chime_start_menu = ttk.Combobox(chime_frame, textvariable=chime_start_var, values=chime_files, state="readonly", width=20)
    chime_start_menu.pack(anchor="w", pady=2)
    tk.Button(chime_frame, text="Play", font=("Arial", 9), command=lambda: play_chime(chime_start_var.get())).pack(anchor="w", pady=2)

    tk.Label(chime_frame, text="Chime at end:", font=("Arial", 10)).pack(anchor="w", pady=2)
    chime_end_menu = ttk.Combobox(chime_frame, textvariable=chime_end_var, values=chime_files, state="readonly", width=20)
    chime_end_menu.pack(anchor="w", pady=2)
    tk.Button(chime_frame, text="Play", font=("Arial", 9), command=lambda: play_chime(chime_end_var.get())).pack(anchor="w", pady=2)

    # Bottom section - Captain Style and buttons
    bottom_inner_frame = tk.LabelFrame(bottom_frame, text="Additional Settings", font=("Arial", 12, "bold"), padx=10, pady=10)
    bottom_inner_frame.pack(fill="x", pady=5)

    tk.Label(bottom_inner_frame, text="Captain Style:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", pady=5)
    ttk.Combobox(bottom_inner_frame, textvariable=style_var, values=["professional", "austere", "friendly", "experienced"], state="readonly", width=20).grid(row=0, column=1, pady=5, sticky="w")

    tk.Button(bottom_inner_frame, text="Browse flight_data.txt", command=browse_flight_data_file, font=("Arial", 11)).grid(row=1, column=0, columnspan=2, pady=10)

    tk.Button(settings_window, text="Confirm", command=submit, font=("Arial", 12), bg="#4CAF50", fg="white").pack(pady=10)

    # Set column weights for better layout
    main_frame.columnconfigure(0, weight=1)
    main_frame.columnconfigure(1, weight=1)
    main_frame.rowconfigure(0, weight=1)

    settings_window.mainloop()

open_settings_window()

# ✅ Load new configuration
config = load_config()
import flask_server
from flask_server import flight_info

# Pokud byla vybrána cesta k flight_data.txt, aktualizujeme ji nyní
if pending_flight_data_path:
    flask_server.update_flight_data_path()

print("🚀 Starting... please wait...")
flask_thread = threading.Thread(target=flask_server.start_flask_server, daemon=True)
flask_thread.start()

# 💾 Variables from configuration
captain_name = config["captain_name"]
first_officer = config["first_officer"]
openai_api_key = config["openai_api_key"]
primary_lang = config["primary_language"]
secondary_langs = config["secondary_languages"]
airport_langs = config["airport_announcement_languages"]
captain_style = config["captain_style"]
flight_data_file = config["flight_data_file"]
generator = config["announcement_generator"]

import announcement_generator
valid_languages = announcement_generator.valid_languages
captain_styles = announcement_generator.captain_styles
selected_languages = []

# 🛫 GUI for flight confirmation
selected_flight = flight_selection.run_gui()

if selected_flight:
    airline_icao = selected_flight.get("airline_icao") or selected_flight.get("icao") or "Unknown"
    safety_videos = announcement_generator.find_safety_videos(airline_icao)

    def confirm_flight():
        global aircraft, airline, flight_duration, safety_announcement_option, selected_safety_video, gate, food_options, beverage_service
        aircraft = aircraft_var.get().strip()
        airline = airline_var.get().strip()
        flight_duration = flight_duration_var.get().strip()
        safety_announcement_option = safety_var.get()
        selected_safety_video = video_var.get()
        gate = gate_var.get().strip()
        food_options = food_options_var.get().strip()
        beverage_service = beverage_service_var.get()

        if not aircraft or not airline or not flight_duration or not gate:
            messagebox.showwarning("Error", "All required fields must be filled out!")
            return

        # Nastav flight_info v flask_server
        flask_server.flight_info = {
            "captain_name": captain_name,
            "first_officer": first_officer,
            "flight_number": selected_flight["flight_number"],
            "origin": selected_flight["origin"],
            "destination": selected_flight["destination"],
            "aircraft": aircraft,
            "airline": airline,
            "flight_duration": flight_duration,  # Používáme "flight_duration" pro konzistenci
            "primary_lang": primary_lang,
            "gate": gate,
            "food_options": food_options,
            "beverage_service": beverage_service
        }
        print(f"flight_info set to: {flask_server.flight_info}")  # Ladící výpis

        flight_window.destroy()
        flight_confirmed.set(True)

    flight_window = tk.Tk()
    flight_window.title("Confirm")

    tk.Label(flight_window, text="Aircraft:", font=("Arial", 12)).pack(pady=5)
    aircraft_var = tk.StringVar(value=selected_flight.get("aircraft", "Boeing 737"))
    tk.Entry(flight_window, textvariable=aircraft_var, font=("Arial", 12), width=30).pack(pady=5)

    tk.Label(flight_window, text="Airline:", font=("Arial", 12)).pack(pady=5)
    airline_var = tk.StringVar(value=selected_flight.get("airline", "Unknown"))
    tk.Entry(flight_window, textvariable=airline_var, font=("Arial", 12), width=30).pack(pady=5)

    tk.Label(flight_window, text="Duration (ex. 2h 15m):", font=("Arial", 12)).pack(pady=5)
    flight_duration_var = tk.StringVar(value=selected_flight.get("duration", "2h 15m"))
    tk.Entry(flight_window, textvariable=flight_duration_var, font=("Arial", 12), width=30).pack(pady=5)

    tk.Label(flight_window, text="Gate:", font=("Arial", 12)).pack(pady=5)
    gate_var = tk.StringVar(value="A1")
    tk.Entry(flight_window, textvariable=gate_var, font=("Arial", 12), width=30).pack(pady=5)

    tk.Label(flight_window, text="Food Options (comma-separated, e.g., sandwich, pasta, salad):", font=("Arial", 12)).pack(pady=5)
    food_options_var = tk.StringVar(value="sandwich, pasta, salad")
    tk.Entry(flight_window, textvariable=food_options_var, font=("Arial", 12), width=30).pack(pady=5)

    tk.Label(flight_window, text="Beverage Service Type:", font=("Arial", 12)).pack(pady=5)
    beverage_service_var = tk.StringVar(value="dry")
    tk.Radiobutton(flight_window, text="Dry Airline (no alcohol)", variable=beverage_service_var, value="dry", font=("Arial", 11)).pack(anchor="w")
    tk.Radiobutton(flight_window, text="Complimentary (free alcohol)", variable=beverage_service_var, value="complimentary", font=("Arial", 11)).pack(anchor="w")
    tk.Radiobutton(flight_window, text="Paid (alcohol for charge)", variable=beverage_service_var, value="paid", font=("Arial", 11)).pack(anchor="w")

    tk.Label(flight_window, text="Safety announcement:", font=("Arial", 12, "bold")).pack(pady=10)
    safety_var = tk.StringVar(value="video")
    tk.Radiobutton(flight_window, text="📼 Use safety video (if exists)", variable=safety_var, value="video", font=("Arial", 11)).pack(anchor="w")
    tk.Radiobutton(flight_window, text="🎙 Generate safety announcement", variable=safety_var, value="generated", font=("Arial", 11)).pack(anchor="w")
    tk.Radiobutton(flight_window, text="⏩ Skip", variable=safety_var, value="skip", font=("Arial", 11)).pack(anchor="w")

    tk.Label(flight_window, text="Choose safety video:", font=("Arial", 12, "bold")).pack(pady=5)
    video_var = tk.StringVar(value=safety_videos[0] if safety_videos else "")
    if safety_videos:
        for video in safety_videos:
            tk.Radiobutton(flight_window, text=os.path.basename(video), variable=video_var, value=video).pack(anchor="w")
    else:
        tk.Label(flight_window, text="❌ No videos available!", fg="red", font=("Arial", 11)).pack()

    submit_button = tk.Button(flight_window, text="Confirm", command=confirm_flight, font=("Arial", 12))
    submit_button.pack(pady=10)

    flight_confirmed = tk.BooleanVar(value=False)
    flight_window.mainloop()

    if not flight_confirmed.get():
        exit()

    print(f"🛫 Confirmed flight: {selected_flight['flight_number']} ({selected_flight['origin']} → {selected_flight['destination']})")

    print("🖥 Starting GUI Flight Phase Monitor...")
    gui_thread = threading.Thread(target=flask_server.start_gui, daemon=True)
    gui_thread.start()

    def monitor_gui():
        while True:
            if not gui_thread.is_alive():
                print("❌ GUI Flight Phase Monitor closed! Ending the script...")
                os._exit(1)
            time.sleep(1)

    monitor_thread = threading.Thread(target=monitor_gui, daemon=True)
    monitor_thread.start()

    print("✅ GUI is running in the background!")

    last_phase = None
    played_safety_announcement = False
    safety_announcement_triggered = False

    config = load_config()
    primary_lang = config["primary_language"]
    all_langs = list(set([primary_lang] + config["secondary_languages"]))
    all_order = config.get("all_language_order", [])
    all_langs_sorted = [lang for lang, _ in sorted(all_order, key=lambda x: x[1])] if all_order else all_langs
    airport_langs = config["airport_announcement_languages"]
    airport_order = config.get("airport_announcement_order", [])
    airport_langs_sorted = [lang for lang, _ in sorted(airport_order, key=lambda x: x[1])] if airport_order else airport_langs
    enable_airport = config.get("enable_airport_announcement", True)
    captain_style = config.get("captain_style", "professional")

    # Main loop
    while True:
        phase = flask_server.flight_data["phase"]

        if phase == "Gate":
            if enable_airport and "AirportBoarding" not in announcement_generator.played_announcements:
                print("🔔 Generating airport boarding announcement...")
                announcement_generator.play_announcement(
                    "AirportBoarding",
                    {
                        "flight_number": selected_flight["flight_number"],
                        "destination": selected_flight["destination"],
                        "airline": airline,
                        "primary_lang": primary_lang,
                        "gate": gate,
                        "food_options": food_options,
                        "beverage_service": beverage_service
                    },
                    flask_server.flight_data,
                    all_langs_sorted,
                    airport_langs_sorted,
                    airport_order,
                    captain_style
                )
                time.sleep(2)

            if "Gate" not in announcement_generator.played_announcements:
                print("🗣 Generating captain's Gate announcement...")
                announcement_generator.play_announcement(
                    "Gate",
                    {
                        "captain_name": captain_name,
                        "first_officer": first_officer,
                        "flight_number": selected_flight["flight_number"],
                        "origin": selected_flight["origin"],
                        "destination": selected_flight["destination"],
                        "aircraft": aircraft,
                        "airline": airline,
                        "flight_duration": flight_duration,
                        "primary_lang": primary_lang,
                        "gate": gate,
                        "food_options": food_options,
                        "beverage_service": beverage_service
                    },
                    flask_server.flight_data,
                    all_langs_sorted,
                    airport_langs_sorted,
                    airport_order,
                    captain_style
                )

        # 🛫 Pushback and safety announcement
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
                    "duration": flight_duration,
                    "primary_lang": primary_lang,
                    "gate": gate,
                    "food_options": food_options,
                    "beverage_service": beverage_service
                },
                flask_server.flight_data,
                all_langs_sorted,
                airport_langs_sorted,
                airport_order,
                captain_style
            )
            time.sleep(5)

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

        # 🗣 Other announcements (kromě LastCall a InflightService)
        if phase != last_phase and phase in announcement_generator.ANNOUNCEMENTS and phase not in ["LastCall", "InflightService"]:
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
                    "duration": flight_duration,
                    "primary_lang": primary_lang,
                    "gate": gate,
                    "food_options": food_options,
                    "beverage_service": beverage_service
                },
                flask_server.flight_data,
                all_langs_sorted,
                airport_langs_sorted,
                airport_order,
                captain_style
            )
            last_phase = phase

        time.sleep(5)