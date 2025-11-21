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
| Physical Pin | BCM | Function  | Connection                           |
|--------------|-----|-----------|---------------------------------------|
| 6            | —   | GND       | Ground for ALL devices                |
| 7            | 4   | GPIO4     | Button                                |
| 8            | 14  | TXD0      | Plantower #1 → RX  (UART0)            |
| 10           | 15  | RXD0      | Plantower #1 ← TX   (UART0)           |
| 11           | 17  | GPIO17    | Fan tachometer                        |
| 27           | 0   | TXD1      | SPS30 → RX (UART1 TX → Pi RX)         |
| 28           | 1   | RXD1      | SPS30 ← TX (UART1 RX ← Pi TX)         |
| 32           | 12  | TXD4      | Plantower #2 → RX (UART4 TX → Pi RX)  |
| 33           | 13  | RXD4      | Plantower #2 ← TX (UART4 RX ← Pi TX)  |
| 37           | 26  | GPIO26    | Plantower power (Relay1)              |
| 38           | 20  | GPIO20    | Heater (Relay2)                       |
| 40           | 21  | GPIO21    | Zero pump  (Relay3)                   |

<img width="2064" height="1185" alt="image" src="https://github.com/user-attachments/assets/e8ecd469-3049-42fc-9901-e12cf2c2a09a" />

> Note: we are skipping UART2 since we are using gpio 4 (physical pin 7) for something else

### changuing UART settings
``` /boot/firmware/config.txt```
```bash
enable_uart=1
dtoverlay=uart1
dtoverlay=uart4
```
### 5V devices:
Particle sensors (3x), level shifters

### 12V devices:
Fan, Pumps, motorized ball valce, heater strip+ (rheostat)
