-- FlyWithLua script pro ukládání letové fáze do TXT souboru

local FILE_PATH = "Resources/plugins/FlyWithLua/Scripts/flight_data.txt"
local last_update = os.clock() -- Čas posledního zápisu
local current_phase = "Unknown" -- Uložená poslední dosažená fáze
local airborne = 0 -- 0 = na zemi, 1 = ve vzduchu (aktivuje se při Cruise)

function save_flight_data()
    -- ✅ Zabráníme příliš častému zápisu
    if os.clock() - last_update < 1 then
        return
    end
    last_update = os.clock()
    
    local groundspeed = get("sim/flightmodel/position/groundspeed") * 1.94384  -- m/s na knots
    local vertical_speed = get("sim/flightmodel/position/vh_ind_fpm")  -- ft/min
    local altitude = get("sim/flightmodel/position/elevation") * 3.28084  -- m na ft
    local on_ground = get("sim/flightmodel/failures/onground_any")
    
    -- Světla (0 = vypnuté, 1 = zapnuté)
    local beacon = get("sim/cockpit/electrical/beacon_lights_on")
    local strobe = get("sim/cockpit/electrical/strobe_lights_on")
    local taxi_light = get("sim/cockpit/electrical/taxi_light_on")
    local landing_light = get("sim/cockpit/electrical/landing_lights_on")
    
    local temperature = get("sim/weather/aircraft/temperature_ambient_deg_c") -- Teplota ve stupních Celsia
    
    -- Získání času v simulaci (UTC)
    local sim_time_sec = get("sim/time/zulu_time_sec")
    local sim_hours = math.floor(sim_time_sec / 3600) % 24
    local sim_minutes = math.floor((sim_time_sec % 3600) / 60)
    local sim_seconds = math.floor(sim_time_sec % 60)
    
    -- Výpočet lokálního času na základě zeměpisné délky
    local longitude = get("sim/flightmodel/position/longitude")
    local timezone_offset = math.floor((longitude + 7.5) / 15) -- Přibližný výpočet časového posunu
    local local_time_sec = sim_time_sec + (timezone_offset * 3600)
    local local_hours = (math.floor(local_time_sec / 3600) % 24)
    local local_minutes = math.floor((local_time_sec % 3600) / 60)
    local local_seconds = math.floor(local_time_sec % 60)

    local phase = "Unknown"

    -- 🚀 **Detekce letové fáze**
    if airborne == 0 then -- Fáze před dosažením Cruise
        if beacon == 0 and strobe == 0 then
            phase = "Gate"
        elseif beacon == 1 and strobe == 0 then
            phase = "Pushback"
        elseif beacon == 1 and strobe == 1 and altitude < 10000 then
            phase = "Takeoff"
        elseif vertical_speed > 500 and altitude > 10000 and strobe == 1 then
            phase = "Climb"
        elseif vertical_speed > -500 and vertical_speed < 500 and altitude > 10000 and strobe == 1 then
            phase = "Cruise"
            airborne = 1 -- Jakmile dosáhne Cruise, přepne se na 1
        elseif vertical_speed < -500 and altitude > 20000 and strobe == 1 then
            phase = "Descent"
            airborne = 1 
        end
    end

    -- Fáze po dosažení Cruise
    if airborne == 1 then
        if vertical_speed > 500 and altitude > 10000 and strobe == 1 then
            phase = "Climb"
            airborne = 1 
        elseif vertical_speed > -500 and vertical_speed < 500 and altitude > 10000 and strobe == 1 then
            phase = "Cruise"
            airborne = 1 
        elseif vertical_speed < -500 and altitude > 20000 and strobe == 1 then
            phase = "Descent"
            airborne = 1 
        elseif altitude < 20000 and altitude > 10000 and strobe == 1 then
            phase = "Approach"
        elseif altitude < 10000 and strobe == 1 then
            phase = "Final"
        elseif beacon == 1 and strobe == 0 and on_ground == 1 then
            phase = "TaxiAfterLanding"
        elseif beacon == 0 and strobe == 0 and on_ground == 1 then
            phase = "Deboarding"
        end
    end
    
    -- 📝 Debug zprávy
    logMsg(string.format("DEBUG: phase=%s, airborne=%d, on_ground=%s, altitude=%.2f, speed=%.2f, beacon=%d, strobe=%d, taxi_light=%d, landing_light=%d, sim_time=%02d:%02d:%02d, local_time=%02d:%02d:%02d", 
        tostring(phase), airborne, tostring(on_ground), altitude, groundspeed, beacon, strobe, taxi_light, landing_light, 
        sim_hours, sim_minutes, sim_seconds, local_hours, local_minutes, local_seconds))
    
    -- 📝 Uložit do TXT souboru
    local file = io.open(FILE_PATH, "w")
    if file then
        file:write(string.format(
            "phase=%s\naltitude=%.2f\nspeed=%.2f\nvertical_speed=%.2f\nbeacon=%d\nstrobe=%d\ntaxi_light=%d\nlanding_light=%d\ntemperature=%.2f\nsim_time=%02d:%02d:%02d\nlocal_time=%02d:%02d:%02d\n",
            phase, altitude, groundspeed, vertical_speed, beacon, strobe, taxi_light, landing_light, temperature,
            sim_hours, sim_minutes, sim_seconds, local_hours, local_minutes, local_seconds
        ))
        file:close()
    end
end

-- ⏳ **Spouští se každou sekundu**
do_every_frame("save_flight_data()")
