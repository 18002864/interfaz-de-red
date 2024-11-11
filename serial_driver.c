#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <termios.h>

// Define packet structure fields
#define TO 0x04       // Example destination address
#define FROM 0x02     // Example source address

// Calculate checksum (as per the format you mentioned)
unsigned char calculate_checksum(unsigned char to, unsigned char from, unsigned char length) {
    return ((to + from + length) ^ 0xFF) + 1;
}

// Function to send the packet over serial
void send_packet(int serial_port, const char *data) {
    unsigned char length = strlen(data);
    unsigned char checksum = calculate_checksum(TO, FROM, length);

    // Create packet
    unsigned char packet[5 + length];
    packet[0] = 'J';
    packet[1] = TO;
    packet[2] = FROM;
    packet[3] = length;
    packet[4] = checksum;
    memcpy(&packet[5], data, length);

    // Send the packet
    write(serial_port, packet, sizeof(packet));
    printf("Sent packet: To=%d, From=%d, Length=%d, Checksum=%d, Data=%s\n",
           TO, FROM, length, checksum, data);
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <data>\n", argv[0]);
        return EXIT_FAILURE;
    }

    const char *data = argv[1];

    printf("------> %s\n", data);

    const char *portname = "/dev/ttyACM0";  // Adjust to your port
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

    tcflush(serial_port, TCIOFLUSH);
    
    // Send the packet with the data from the HTTP server
    send_packet(serial_port, data);

    // Close the serial port
    close(serial_port);

    return 0;
}
