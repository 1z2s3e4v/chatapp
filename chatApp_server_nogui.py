import tkinter as tk
import socket
import threading

import math
import time
import os

server = None
#HOST_ADDR = "127.0.0.1"
HOST_ADDR = "10.140.0.5"
HOST_PORT = 55
client_name = " "
clients = []
clients_names = []


# Start server function
def start_server():
    global server, HOST_ADDR, HOST_PORT # code is fine without this

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(socket.AF_INET)
    print(socket.SOCK_STREAM)

    server.bind((HOST_ADDR, HOST_PORT))
    server.listen(5)  # server is listening for client connection

    threading._start_new_thread(accept_clients, (server, " "))

def accept_clients(the_server, y):
    while True:
        client, addr = the_server.accept()
        clients.append(client)

        # use a thread so as not to clog the gui thread
        threading._start_new_thread(receiving_client_message_and_send, (client, addr))


# Function to receive message from current client AND
# Send that message to other clients
def receiving_client_message_and_send(client_connection, client_ip_addr):
    global server, client_name, clients, clients_addr
    client_msg = " "
    buffer_size = 4096
    fileType = 0 # 0:msg, 1:img, 2:other
    download_file_name = ""

    # send welcome message to client
    client_name  = client_connection.recv(buffer_size).decode()
    welcome_msg = "Welcome " + client_name + ". Use 'exit' to quit"
    client_connection.send(welcome_msg.encode())

    clients_names.append(client_name)

    while True:
        try:
            if fileType == 1: # image
                fileType = 0
                recv_buffer_size = buffer_size
                buffer_size = 4096
                # receiving image
                data = client_connection.recv(recv_buffer_size)
                #time.sleep(1)
                myfile = open("received_image.jpg", 'wb')
                myfile.write(data)
                myfile.close()
                print("Recieved image.")
                # sending image to other
                idx = get_client_index(clients, client_connection)
                sending_client_name = clients_names[idx]
                for c in clients:
                    if c != client_connection:
                        server_msg = str(sending_client_name + "-> send a image:")
                        c.send(server_msg.encode())
                        # send image_head
                        #time.sleep(0.5)
                        c.send(("IMAGESIZE %s" % str(recv_buffer_size)).encode())
                        # send image
                        time.sleep(1)
                        c.sendall(data)
                        #time.sleep(1)
                        print("Sending image")
            elif fileType == 2: # file
                fileType = 0
                recv_buffer_size = buffer_size
                buffer_size = 4096
                # receiving file
                data = client_connection.recv(recv_buffer_size)
                myfile = open(download_file_name, 'wb')
                myfile.write(data)
                myfile.close()
                print("Recieved file", download_file_name)
                # sending info to other user
                idx = get_client_index(clients, client_connection)
                sending_client_name = clients_names[idx]
                for c in clients:
                    if c != client_connection:
                        server_msg = str(sending_client_name + "-> send a file \'" + download_file_name + "\' (size=" + str(recv_buffer_size) + ")")
                        c.send(server_msg.encode())

                        # send file_head
                        time.sleep(0.5)
                        c.send(("FILESIZE %s FILENAME %s" % (str(recv_buffer_size), os.path.basename(download_file_name))).encode())
                        # send file
                        c.sendall(data)
            else: # message
                data = client_connection.recv(buffer_size).decode()
                if not data: break
                if data == "exit": break
                print("received msg: \'%s\'" % data)
                if data[0:9] == "IMAGESIZE":
                    data_size = int(data.split()[1])
                    print("Recieving a image with size %s." % data_size)
                    buffer_size = 4096*(math.ceil(data_size/4096))
                    fileType = 1
                elif data[0:8] == "FILESIZE":
                    # FILESIZE 123 FILENAME 123.pdf
                    data_size = int(data.split()[1])
                    download_file_name = str(data.split()[3])
                    print("Recieving a file \'%s\' with size %s." %(download_file_name ,data_size))
                    buffer_size = 4096*(math.ceil(data_size/4096))
                    fileType = 2
                else:
                    client_msg = data
                    idx = get_client_index(clients, client_connection)
                    sending_client_name = clients_names[idx]
                    for c in clients:
                        if c != client_connection:
                            server_msg = str(sending_client_name + "->" + client_msg)
                            c.send(server_msg.encode())
        except:
            #print("Unexpected error occur when server receiving data.")
            continue

    # find the client index then remove from both lists(client name list and connection list)
    idx = get_client_index(clients, client_connection)
    del clients_names[idx]
    del clients[idx]
    server_msg = "BYE!"
    client_connection.send(server_msg.encode())
    client_connection.close()

# Return the index of the current client in the list of clients
def get_client_index(client_list, curr_client):
    idx = 0
    for conn in client_list:
        if conn == curr_client:
            break
        idx = idx + 1

    return idx

start_server()
while(1):
    continue
