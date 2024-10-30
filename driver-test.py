from serial import Serial
import struct
import time

# Adjust the port name as per your system
SERIAL_PORT = '/dev/ttyUSB0'  # Replace with 'COMx' on Windows (e.g., 'COM3')
BAUDRATE = 115200

def calculate_checksum(to, from_, length):
    # Calculates checksum by summing fields and inverting bits (similar to XOR with 0xFF + 1)
    return ((to + from_ + length) ^ 0xFF) + 1

def send_packet(ser, to, from_, data):
    # Packet structure: to, from, length, checksum, data
    length = len(data)
    checksum = calculate_checksum(to, from_, length)

    # Pack the header fields as bytes
    header = struct.pack('BBBB', to, from_, length, checksum)
    packet = header + data.encode('utf-8')

    # Send packet
    ser.write(packet)
    print(f"Sent packet: To={to}, From={from_}, Length={length}, Checksum={checksum}, Data={data}")

def main():
    with serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1) as ser:
        time.sleep(2)  # Wait for the serial connection to initialize

        # Example packet data
        to = 0x4
        from_ = 0x2
        data = "Hello from the driver!"

        send_packet(ser, to, from_, data)

if __name__ == '__main__':
    main()
