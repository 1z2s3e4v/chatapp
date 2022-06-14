import tkinter as tk
from tkinter import filedialog as fd
import socket
import threading

import math
import time
import os

window = tk.Tk()
window.title("Client")
username = " "


topFrame = tk.Frame(window)
lblName = tk.Label(topFrame, text = "Name:").pack(side=tk.LEFT)
entName = tk.Entry(topFrame)
entName.pack(side=tk.LEFT)
btnConnect = tk.Button(topFrame, text="Connect", command=lambda : connect())
btnConnect.pack(side=tk.LEFT)
#btnConnect.bind('<Button-1>', connect)
topFrame.pack(side=tk.TOP)

displayFrame = tk.Frame(window)
lblLine = tk.Label(displayFrame, text="*********************************************************************").pack()
scrollBar = tk.Scrollbar(displayFrame)
scrollBar.pack(side=tk.RIGHT, fill=tk.Y)
tkDisplay = tk.Text(displayFrame, height=20, width=55, selectbackground="yellow", selectforeground="black")
tkDisplay.pack(side=tk.LEFT, fill=tk.Y, padx=(5, 0))
tkDisplay.tag_config("tag_your_message", foreground="blue")
scrollBar.config(command=tkDisplay.yview)
tkDisplay.config(yscrollcommand=scrollBar.set, background="#F4F6F7", highlightbackground="grey", state="disabled")
displayFrame.pack(side=tk.TOP)

display_image_list = []
download_path = "D:\\"


bottomFrame = tk.Frame(window)
tkMessage = tk.Text(bottomFrame, height=2, width=40)
tkMessage.pack(side=tk.LEFT, padx=(5, 13), pady=(5, 10))
tkMessage.config(highlightbackground="grey", state="disabled")
tkMessage.bind("<Return>", (lambda event: getChatMessage(tkMessage.get("1.0", tk.END))))
btnSendImage = tk.Button(bottomFrame, text="Send File", command=lambda : send_file())
btnSendImage.pack(side=tk.LEFT)
btnSendImage.config(state=tk.DISABLED)
bottomFrame.pack(side=tk.BOTTOM)


def connect():
    global username, client
    if len(entName.get()) < 1:
        tk.messagebox.showerror(title="ERROR!!!", message="You MUST enter your first name <e.g. John>")
    else:
        username = entName.get()
        connect_to_server(username)


# network client
client = None
#HOST_ADDR = "127.0.0.1"
HOST_ADDR = "34.80.243.231"
HOST_PORT = 55

def connect_to_server(name):
    global client, HOST_PORT, HOST_ADDR
    try:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect((HOST_ADDR, HOST_PORT))
        client.send(name.encode()) # Send name to server after connecting

        entName.config(state=tk.DISABLED)
        btnConnect.config(state=tk.DISABLED)
        btnSendImage.config(state=tk.NORMAL)
        tkMessage.config(state=tk.NORMAL)

        # start a thread to keep receiving message from server
        # do not block the main thread :)
        threading._start_new_thread(receive_message_from_server, (client, "m"))
    except Exception as e:
        tk.messagebox.showerror(title="ERROR!!!", message="Cannot connect to host: " + HOST_ADDR + " on port: " + str(HOST_PORT) + " Server may be Unavailable. Try again later")


def receive_message_from_server(sck, m):
    global display_image_list, username
    buffer_size = 4096
    fileType = 0 # 0:msg, 1:img, 2:other
    global download_path
    download_file_name = ""
    while True:
        try:
            if fileType == 1 : # image
                fileType = 0
                recv_buffer_size = buffer_size
                buffer_size = 4096
                # receiving image
                data = sck.recv(recv_buffer_size)
                myfile = open(username+"_received_image.jpg", 'wb')
                myfile.write(data)
                myfile.close()
                print("Recieved image.")
                # Show on GUI
                #time.sleep(1)
                tkDisplay.config(state=tk.NORMAL)
                my_image = tk.PhotoImage(file=username+"_received_image.jpg")
                display_image_list.append(my_image)
                tkDisplay.insert(tk.END, "\n")
                tkDisplay.image_create(tk.END, image=display_image_list[-1])
                tkDisplay.config(state=tk.DISABLED)
                tkDisplay.see(tk.END)

            elif fileType == 2 : # file
                fileType = 0
                recv_buffer_size = buffer_size
                buffer_size = 4096
                # receiving file
                data = sck.recv(recv_buffer_size)
                myfile = open(download_file_name, 'wb')
                myfile.write(data)
                myfile.close()
                print("Recieved file.")
                # Show on GUI
                time.sleep(0.5)
                tkDisplay.config(state=tk.NORMAL)
                tkDisplay.insert(tk.END, "\nFile \'"+download_file_name+"\' has been downloaded.")
                tkDisplay.config(state=tk.DISABLED)
                tkDisplay.see(tk.END)
            else: # message
                from_server = sck.recv(buffer_size).decode()
                if not from_server: break
                # display message from server on the chat window

                # enable the display area and insert the text and then disable.
                # why? Apparently, tkinter does not allow us insert into a disabled Text widget :(
                print("received msg: \'%s\'" % from_server)
                if from_server[0:9] == "IMAGESIZE":
                    data_size = int(from_server.split()[1])
                    print("Recieving a image with size %s." % data_size)
                    buffer_size = 4096*(math.ceil(data_size/4096))
                    fileType = 1
                elif from_server[0:8] == "FILESIZE":
                    # FILESIZE 123 FILENAME 123.pdf
                    data_size = int(from_server.split()[1])
                    download_file_name = str(from_server.split()[3])
                    print("Recieving a file \'%s\' with size %s." %(download_file_name ,data_size))
                    buffer_size = 4096*(math.ceil(data_size/4096))
                    fileType = 2
                else:
                    texts = tkDisplay.get("1.0", tk.END).strip()
                    tkDisplay.config(state=tk.NORMAL)
                    if len(texts) < 1:
                        tkDisplay.insert(tk.END, from_server)
                    else:
                        tkDisplay.insert(tk.END, "\n\n"+ from_server)
                    #if("-> send a file" in from_server):
                    tkDisplay.config(state=tk.DISABLED)
                    tkDisplay.see(tk.END)
                    # print("Server says: " +from_server)
        except:
            #print("Unexpected error occur when server receiving data.")
            continue

    sck.close()
    window.destroy()


def getChatMessage(msg):

    msg = msg.replace('\n', '')
    texts = tkDisplay.get("1.0", tk.END).strip()

    # enable the display area and insert the text and then disable.
    # why? Apparently, tkinter does not allow use insert into a disabled Text widget :(
    tkDisplay.config(state=tk.NORMAL)
    if len(texts) < 1:
        tkDisplay.insert(tk.END, "You->" + msg, "tag_your_message") # no line
    else:
        tkDisplay.insert(tk.END, "\n\n" + "You->" + msg, "tag_your_message")

    tkDisplay.config(state=tk.DISABLED)

    send_mssage_to_server(msg)

    tkDisplay.see(tk.END)
    tkMessage.delete('1.0', tk.END)


def send_mssage_to_server(msg):
    client_msg = str(msg)
    client.send(client_msg.encode())
    if msg == "exit":
        client.close()
        window.destroy()
    print("Sending message")

def send_file():
    fileName=fd.askopenfilename()
    if((".jpg" in fileName) or (".png" in fileName)):
        send_image(fileName)
    else:
        # Show on GUI
        tkDisplay.config(state=tk.NORMAL)
        tkDisplay.insert(tk.END, "\n\n" + "You-> send a file \'"+os.path.basename(fileName)+"\'.")
        tkDisplay.config(state=tk.DISABLED)
        tkDisplay.see(tk.END)

        # Send to server
        myfile = open(fileName, 'rb')
        bytes = myfile.read()
        size = len(bytes)
        # send file_head
        client.send(("FILESIZE %s FILENAME %s" % (str(size), os.path.basename(fileName))).encode())
        time.sleep(0.5)
        # send file
        client.sendall(bytes)
        print("Sending file",fileName)

def send_image(fileName):
    #fileName=fd.askopenfilename(filetypes=[("Image File",'.jpg')])
    global display_image_list
    # Show on GUI
    tkDisplay.config(state=tk.NORMAL)
    tkDisplay.insert(tk.END, "\n\n" + "You-> send a image:\n")
    my_image = tk.PhotoImage(file=fileName)
    display_image_list.append(my_image)
    tkDisplay.image_create(tk.END, image=display_image_list[-1])
    tkDisplay.config(state=tk.DISABLED)
    tkDisplay.see(tk.END)

    # Send to server
    myfile = open(fileName, 'rb')
    bytes = myfile.read()
    size = len(bytes)
    # send image_head
    client.send(("IMAGESIZE %s" % str(size)).encode())
    time.sleep(1)
    # send image
    client.sendall(bytes)
    print("Sending image")

window.mainloop()