#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>

// Define packet structure fields
#define TO 0x04       // Example destination address
#define FROM 0x02     // Example source address
#define DATA "Hello from the driver!"  // Example data to send

// Calculate checksum (as per the format you mentioned)
unsigned char calculate_checksum(unsigned char to, unsigned char from, unsigned char length) {
    return ((to + from + length) ^ 0xFF) + 1;
}

// Function to send the packet over serial
void send_packet(int serial_port) {
    unsigned char length = strlen(DATA);
    unsigned char checksum = calculate_checksum(TO, FROM, length);

    // Create packet
    unsigned char packet[4 + length];
    packet[0] = TO;
    packet[1] = FROM;
    packet[2] = length;
    packet[3] = checksum;
    memcpy(&packet[4], DATA, length);

    // Send the packet
    write(serial_port, packet, sizeof(packet));
    printf("Sent packet: To=%d, From=%d, Length=%d, Checksum=%d, Data=%s\n",
           TO, FROM, length, checksum, DATA);
}

int main() {
    const char *portname = "/dev/ttyUSB0";  // Adjust to your port
    int serial_port = open(portname, O_RDWR | O_NOCTTY | O_NDELAY);

    if (serial_port == -1) {
        perror("Unable to open port");
        return EXIT_FAILURE;
    }

    // Configure serial port
    struct termios options;
    tcgetattr(serial_port, &options);
    cfsetispeed(&options, B115200);
    cfsetospeed(&options, B115200);
    options.c_cflag |= (CLOCAL | CREAD);
    options.c_cflag &= ~PARENB; // No parity
    options.c_cflag &= ~CSTOPB; // 1 stop bit
    options.c_cflag &= ~CSIZE;  // Clear data size bits
    options.c_cflag |= CS8;     // 8 data bits

    tcsetattr(serial_port, TCSANOW, &options);

    // Send the packet
    send_packet(serial_port);

    // Close the serial port
    close(serial_port);

    return 0;
}
