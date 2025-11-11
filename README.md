# SensORV6
This Readme file contains information on the building and production of a Oregon SensOR box. The original information is found [here](https://github.com/ParticulateSensOR/SensORV6). Kairos here! I am building this as an expansion of a [project](https://github.com/kairosbrightside/sps30-pi) I did last summer (electrical documentation can be found there for the SPS30 sensor). I was supposed to do this like 2 months ago but I took too long on the autosampler `</3`. 

# Purpose
Sensor interface for real-time particulate monitoring using the SPS30 and Raspberry Pi, with CSV logging support. My group wants a met station so it is possible I will expand in that direction too if time and money allow. 


# Equipment list 
| Component                  | Description / Model                                                                 | Notes                          | Have? |
|----------------------------|-------------------------------------------------------------------------------------|--------------------------------|-------|
| PM2.5 Sensor               | Plantower PMs5003ST                                                                 | Measures particulate matter    | ☑️    |
| PM2.5 Sensor               | Sensirion SPS30 sensor                                                              | Measures particulate matter    | ☑️    |
| Power Supply               | RID-65A Meanwell (5V/12V) or RT-65D (5V/24V/12V)                                    | Provides power etc             | ☑️    |
| Computer                   | Raspberry Pi 5                                                                      | Main system controller         | ☑️    |
| SD Card                    | SanDisk 64 GB SD Card                                                               | Storage for OS & data          | ☑️    |
| Auto-Zero Valve            | US Solid Motorized Ball Valve                                                       | Valve                          | ☑️    |
| 2x6 Terminal block         | [Amazon Link](https://www.amazon.com/dp/B09D3BV22M?ref=ppx_yo2ov_dt_b_fed_asin_title) | Makes wiring easier           | ☑️    |
| Heating Element            | [Amazon Link](https://www.amazon.com/dp/B0CLS34QN2?ref=ppx_yo2ov_dt_b_fed_asin_title) | Heating                      | ☑️    |
| GPIO Terminal Block w/LED  | [Amazon Link](https://www.amazon.com/dp/B09QXR6RL7?ref=ppx_yo2ov_dt_b_fed_asin_title) | Easier GPIO wiring + indicators | ☑️    |
| Relay Board / RPi Hat      | [Amazon Link](https://www.amazon.com/dp/B07CZL2SKN?ref=ppx_yo2ov_dt_b_fed_asin_title) | Turns stuff on and off       | ☑️    |
| Diaphragm Pump             | <Will Insert Later>                                                                 | Supplies clean reference air   | ☑️    |
| Rheostat                   | <Will Insert Later>                                                                 | Adjusts current / heating power | ☑️    |
| Sensor Box                 | <Will Insert Later>                                                                 | Enclosure for system           | ☑️    |
| 80 mm computer fan         | generic?                                                                            | Fan                            | ☑️    |

Plus wire, connectors, filament, screws, tools, etc?

# Picture
[![SensOR box](images/sensORbox.png)](images/sensORbox.pdf)

# Relation to E&M
It's got circuits! I need to apply Ohm's Law, Kirchoff's Laws, and power calculations... I can also write about how the particle sensors use optical scattering as a detection method (I think that counts?).

Plantower sensor pinout
<img width="874" height="399" alt="image" src="https://github.com/user-attachments/assets/1f3c9a76-47be-40a2-8d39-d621451f01c3" />



### wiring table 
| Function                    | Device / Load                          | Pi GPIO (BCM)            | Direction         | Voltage Logic                 | Connects to / Notes                                                                            |
| --------------------------- | -------------------------------------- | ------------------------ | ----------------- | ----------------------------- | ---------------------------------------------------------------------------------------------- |
| **User Button**             | Momentary push-button                  | **4**                    | Input (pull-up)   | 3.3 V logic                   | One side → GPIO 4, other → GND. Internal pull-up keeps HIGH; press = LOW.                      |
| **Heater Control**          | Relay Channel 1 (on relay board / HAT) | **20**                   | Output            | 3.3 V logic → 5 V relay input | Drives heater relay. Relay VCC → 5 V; GND → Pi GND. COM → 12 V, NO → heater +. Heater – → GND. |
| **Zero Control Line**       | PMS5003ST “zero” valve or flag         | **21**                   | Output            | 3.3 V                         | Set LOW = zero active. Used by Plantower script.                                               |
| **Fan Tachometer**          | 3- or 4-wire PC fan tach signal        | **5**                    | Input (pull-up)   | 3.3 V                         | Fan yellow (tach) → GPIO 5; fan black (GND) → Pi GND. Internal pull-up OK.                     |
| **Fan Power (on/off)**      | Fan (+12 V load)                       | *(optional)* e.g. **16** | Output            | 3.3 V logic → 5 V relay input | Relay COM → 12 V, NO → fan +. Fan – → GND.                                                     |
| **Pump Power**              | Diaphragm pump                         | *(optional)* e.g. **17** | Output            | 3.3 V logic → 5 V relay input | Relay COM → 12 V, NO → pump +. Pump – → GND.                                                   |
| **Valve Power**             | Auto-zero ball valve                   | *(optional)* e.g. **18** | Output            | 3.3 V logic → 5 V relay input | Relay COM → 12 V or 24 V (per valve). Valve – → GND.                                           |
| **Plantower PM Sensor**     | PMS5003ST                              | **TX 14 / RX 15**        | UART TX/RX        | 3.3 V logic                   | Pi TX → sensor RX; Pi RX → sensor TX; sensor VCC → 5 V; GND → Pi GND.                          |
| **Sensirion PM Sensor**     | SPS30                                  | **SDA 2 / SCL 3**        | I²C bus           | 3.3 V logic (pulled up on Pi) | SDA → GPIO 2; SCL → GPIO 3; VCC → 5 V; GND → Pi GND.                                           |
| **Power to Pi**             | Mean Well RT-65D (5 V rail)            | —                        | Input             | 5 V DC                        | 5 V → Pi USB-C or 5 V GPIO header; GND → Pi GND.                                               |
| **Power to Sensors**        | PMS5003ST, SPS30                       | —                        | Output (from PSU) | 5 V DC                        | From Mean Well 5 V rail (via terminal block).                                                  |
| **Power to Relays / Loads** | Heater, Fan, Pump, Valve               | —                        | Output (from PSU) | 12 V or 24 V DC               | 12 V rail feeds relay COM terminals and loads.                                                 |
| **Common Ground**           | All devices                            | —                        | —                 | —                             | **All grounds must be tied together** (Pi GND = sensor GND = relay GND = PSU GND).             |

