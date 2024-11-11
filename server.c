#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <ctype.h>
#include <stdbool.h>

#define PORT 8080
#define BUFFER_SIZE 4096
#define MAX_MESSAGE_SIZE 1024
#define MAX_ELEMENTS 20
#define RESPONSE_LIST_SIZE 24

// Global variables matching Python implementation
char* last_post_data = NULL;
char response_list[RESPONSE_LIST_SIZE][3] = {"00"};  // Initialize with "0"
char message[MAX_MESSAGE_SIZE] = "";
char* message_elements[MAX_ELEMENTS];
int message_elements_count = 0;

// Protocol variables
char* protocol_request = "";
char* protocol_response = "";
const char* reserved_one = "0";
const char* reserved_two = "00";
const char* sent_request = "304006011";

// Structures to match Python dictionaries
typedef struct {
    char* key;
    int position;
    int value;
} ProtocolSentRequest;

typedef struct {
    char* key;
    int position;
    int value;
} DeviceVD;

// Function declarations
void handle_options_request(int client_socket);
void handle_post_request(int client_socket, char* buffer);
void DEVICE_ACTIVATION(const char* device_g1, const char* g1, const char* device_g2, 
                      const char* g2, const char* extra_value);
void DEVICE_DEACTIVATION(const char* device_g1, const char* g1, const char* device_g2, const char* g2);
void MESSAGE_LCD(const char* group, const char* message_content);
void SET_LCD(bool set_state_value, const char* message_part);

// Helper function to convert string to uppercase
void to_upper(char* str) {
    for(int i = 0; str[i]; i++) {
        str[i] = toupper(str[i]);
    }
}

// Protocol request dictionary initialization
ProtocolSentRequest protocol_sent_request_dictionary[] = {
    {"LCD", 5, 0},
    {"SW0", 2, 1},
    {"SW1", 2, 2},
    {"SLIDERS", 2, 3},
    {"PICKER", 2, 4},
    {"HEAT", 5, 5},
    {"LEDRED", 5, 6},
    {"LEDGRN", 5, 7},
    {"FAN", 5, 8},
    {"LEDRGB", 5, 9}
};

// Function to find protocol request entry
ProtocolSentRequest* find_protocol_request(const char* key) {
    int size = sizeof(protocol_sent_request_dictionary) / sizeof(protocol_sent_request_dictionary[0]);
    for(int i = 0; i < size; i++) {
        if(strcmp(protocol_sent_request_dictionary[i].key, key) == 0) {
            return &protocol_sent_request_dictionary[i];
        }
    }
    return NULL;
}

void handle_request(int client_socket) {
    char buffer[BUFFER_SIZE] = {0};
    int bytes_read = read(client_socket, buffer, BUFFER_SIZE);
    
    if(bytes_read < 0) {
        perror("Error reading request");
        return;
    }

    // Parse request method
    if(strncmp(buffer, "OPTIONS", 7) == 0) {
        handle_options_request(client_socket);
    }
    else if(strncmp(buffer, "POST", 4) == 0) {
        handle_post_request(client_socket, buffer);
    }
}

void handle_options_request(int client_socket) {
    char *response = "HTTP/1.1 200 OK\r\n"
                    "Access-Control-Allow-Origin: *\r\n"
                    "Access-Control-Allow-Methods: POST, OPTIONS\r\n"
                    "Access-Control-Allow-Headers: Content-Type\r\n"
                    "\r\n";
    
    write(client_socket, response, strlen(response));
}

void handle_post_request(int client_socket, char* buffer) {
    // Extract content length
    char* content_length_str = strstr(buffer, "Content-Length: ");
    if(!content_length_str) {
        return;
    }
    
    int content_length = atoi(content_length_str + 16);
    
    // Find start of POST data
    char* post_data = strstr(buffer, "\r\n\r\n");
    if(!post_data) {
        return;
    }
    post_data += 4;  // Skip \r\n\r\n
    
    // Process message
    if(strlen(post_data) >= 24) {
        // Convert hex to string starting from position 24
        char hex_str[3] = {0};
        char ascii_str[MAX_MESSAGE_SIZE] = {0};
        int j = 0;
        
        for(int i = 24; post_data[i] && post_data[i+1]; i += 2) {
            hex_str[0] = post_data[i];
            hex_str[1] = post_data[i+1];
            ascii_str[j++] = (char)strtol(hex_str, NULL, 16);
        }
        
        strncpy(message, ascii_str, MAX_MESSAGE_SIZE-1);
        to_upper(message);
        
        // Split message into elements
        char* token = strtok(message, " ");
        message_elements_count = 0;
        while(token && message_elements_count < MAX_ELEMENTS) {
            message_elements[message_elements_count++] = strdup(token);
            token = strtok(NULL, " ");
        }
        
        // Process message elements
        if(message_elements_count > 0) {
            for(int i = 0; i < message_elements_count; i++) {
                if(strcmp(message_elements[i], "ACT") == 0) {
                    if(i + 1 < message_elements_count) {
                        // Handle activation
                        char* device_g1 = message_elements[0];
                        char* g1 = message_elements[1];
                        char* device_g2 = message_elements[3];
                        char* g2 = message_elements[4];
                        char* extra_value = (message_elements_count > 5) ? message_elements[5] : NULL;
                        
                        DEVICE_ACTIVATION(device_g1, g1, device_g2, g2, extra_value);
                    }
                }
                // Add other keyword handlers here (DEACT, SET, LCD)
            }
        }
    }
    
    // Send response
    char *response_header = "HTTP/1.1 200 OK\r\n"
                          "Content-Type: text/plain\r\n"
                          "Access-Control-Allow-Origin: *\r\n"
                          "\r\n";
    
    write(client_socket, response_header, strlen(response_header));
    if(last_post_data) {
        write(client_socket, last_post_data, strlen(last_post_data));
    }
}

void DEVICE_ACTIVATION(const char* device_g1, const char* g1, const char* device_g2, 
                      const char* g2, const char* extra_value) {
    // Implementation of device activation logic
    ProtocolSentRequest* get_control = find_protocol_request(device_g1);
    ProtocolSentRequest* get_device = find_protocol_request(device_g2);
    
    if(!get_control || !get_device) {
        return;
    }
    
    char protocol_response[100] = {0};
    sprintf(protocol_response, "%s%s%s%s%d0%d1", 
            g1 + 1,  // Skip 'G' in group number
            reserved_one, 
            g2 + 1,  // Skip 'G' in group number
            reserved_two,
            get_control->value,
            get_device->value);
    
    if(extra_value) {
        strcat(protocol_response, extra_value);
    }
    
    if(strlen(protocol_response) >= 9 && strlen(protocol_response) <= 17) {
        printf("APP --> Protocol Response: %s\n", protocol_response);
    }
}

int main() {
    int server_fd, client_socket;
    struct sockaddr_in address;
    int opt = 1;
    int addrlen = sizeof(address);
    
    if((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("Socket creation failed");
        exit(EXIT_FAILURE);
    }
    
    if(setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt))) {
        perror("Setsockopt failed");
        exit(EXIT_FAILURE);
    }
    
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);
    
    if(bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("Bind failed");
        exit(EXIT_FAILURE);
    }
    
    if(listen(server_fd, 3) < 0) {
        perror("Listen failed");
        exit(EXIT_FAILURE);
    }
    
    printf("Server listening on port %d...\n", PORT);
    
    while(1) {
        if((client_socket = accept(server_fd, (struct sockaddr *)&address, 
                                 (socklen_t*)&addrlen)) < 0) {
            perror("Accept failed");
            continue;
        }
        
        handle_request(client_socket);
        close(client_socket);
    }
    
    return 0;
}