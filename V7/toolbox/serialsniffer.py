import serial

def sniff(port, baud):
    print(f"\n--- {port} @ {baud} ---")

    try:
        with serial.Serial(port, baudrate=baud, timeout=2) as ser:
            data = ser.read(100)
            print(data)
    except Exception as e:
        print("Error:", e)


# Plantower sensors
sniff('/dev/ttyAMA1', 9600)
sniff('/dev/ttyAMA4', 9600)

# SPS30
sniff('/dev/ttyAMA0', 115200)