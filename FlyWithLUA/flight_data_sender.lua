-- FlyWithLua script pro ukládání letové fáze do TXT souboru

local FILE_PATH = "Resources/plugins/FlyWithLua/Scripts/flight_data.txt"
local last_update = os.clock() -- Čas posledního zápisu

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

    local phase = "Unknown"

    -- 🚀 **Detekce letové fáze**
    if groundspeed < 1 and on_ground == 1 then
        phase = "Gate"
    elseif groundspeed > 1 and groundspeed < 5 then
        phase = "Pushback"
    elseif groundspeed >= 5 and groundspeed < 50 and on_ground == 1 then
        phase = "Taxi"
    elseif groundspeed > 50 and altitude < 50 then
        phase = "Takeoff"
    elseif vertical_speed > 100 and altitude > 50 then
        phase = "Climb"
    elseif vertical_speed > -100 and vertical_speed < 100 and altitude > 30000 then
        phase = "Cruise"
    elseif vertical_speed < -100 and altitude > 5000 then
        phase = "Descent"
    elseif altitude < 5000 and groundspeed > 50 then
        phase = "Approach"
    elseif altitude < 1000 then
        phase = "Final"
    elseif on_ground == 1 and groundspeed > 0 then
        phase = "Landing"
    elseif on_ground == 1 and groundspeed < 30 then
        phase = "TaxiAfterLanding"
    elseif on_ground == 1 and groundspeed == 0 then
        phase = "Deboarding"
    end

    -- 🎛 **Světla ovlivňující fázi letu**
    if beacon == 1 and phase == "Gate" then
        phase = "Pushback"
    end
    if strobe == 1 and (phase == "Taxi" or phase == "Takeoff" or phase == "Gate" or phase == "Pushback") then
        phase = "Takeoff"
    end
    if taxi_light == 1 and phase == "Taxi" then
        phase = "Taxi (Lights On)"
    end
    if landing_light == 1 and phase == "Final" then
        phase = "Final Approach (Landing Lights)"
    end



    -- 📝 Uložit do TXT souboru
    local file = io.open(FILE_PATH, "w")
    if file then
        file:write(string.format(
            "phase=%s\naltitude=%.2f\nspeed=%.2f\nvertical_speed=%.2f\nbeacon=%d\nstrobe=%d\ntaxi_light=%d\nlanding_light=%d\ntemperature=%.2f\n",
            phase, altitude, groundspeed, vertical_speed, beacon, strobe, taxi_light, landing_light, temperature
        ))
        file:close()
    end
end

-- ⏳ **Spouští se každou sekundu**
do_every_frame("save_flight_data()")
