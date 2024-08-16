#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <sys/socket.h>
#include <arpa/inet.h>

#define PORT 5000
#define BACKLOG 1024  // Increased backlog parameter

void handle_connection(int client_socket) {
    char buffer[1024] = {0};
    const char* response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 16\r\n\r\nHello from App!\n";

    // Simulate a 3-second delay
    sleep(3);

    send(client_socket, response, strlen(response), 0);
    close(client_socket);
}

int main() {
    int server_socket, client_socket;
    struct sockaddr_in server_address, client_address;
    socklen_t client_length;

    // Create the server socket
    server_socket = socket(AF_INET, SOCK_STREAM, 0);
    if (server_socket == -1) {
        perror("socket");
        exit(1);
    }

    // Set up the server address
    memset(&server_address, 0, sizeof(server_address));
    server_address.sin_family = AF_INET;
    server_address.sin_addr.s_addr = INADDR_ANY;
    server_address.sin_port = htons(PORT);

    // Bind the socket to the server address
    if (bind(server_socket, (struct sockaddr*)&server_address, sizeof(server_address)) == -1) {
        perror("bind");
        exit(1);
    }

    // Listen for incoming connections
    if (listen(server_socket, BACKLOG) == -1) {
        perror("listen");
        exit(1);
    }

    printf("Server listening on port %d\n", PORT);

    while (1) {
        client_length = sizeof(client_address);
        client_socket = accept(server_socket, (struct sockaddr*)&client_address, &client_length);
        if (client_socket == -1) {
            perror("accept");
            continue;
        }

        // Handle the connection in a separate thread or process
        handle_connection(client_socket);
    }

    close(server_socket);
    return 0;
}
