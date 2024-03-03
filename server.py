import socket
import threading


def get_local_ip():
    try:
        # Create a socket object and connect to an external server to get back IP address of local machine
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "Unable to determine IP address"

PORT = 5050
SERVER = get_local_ip() #Instead of hard coding in the IP Address this gets the IP Address of local machines
ADDRESS = (SERVER,PORT) #This is the exact address with matching IP and Port number for the server
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!disconnect"

serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)   #SOCK_STREAM is needed for TCP server
serverSocket.bind(ADDRESS)

clientStatus = {}           #Mapping clients usernames to their current status on the server, active or hidden
activeTCPClientsUsername = {}  #Mapping clients usernames to their TCP IP and Port numbers
activeUDPClientsUsername = {}   #Mapping clients usernames to their UDP IP and Port numbers

help_message = "Available Commands:\n" \
                   "- !help: Display a list of available commands.\n" \
                   "- !list: Display a list of active clients.\n" \
                   "- !send <recipientUsername> <message>: Send a message to another client.\n" \
                    "- !broadcast <message>: Broadcast a message to all other active clients.\n" \
                    "- !hide: Hide yourself to not appear to any other client\n" \
                    "- !active: Set yourself as active to be seen by other clients\n" \
                   "- !disconnect: Disconnect from the server.\n"

def handleClient(connectionSocket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    connected = True
    try:
        while connected:
            msg = connectionSocket.recv(2048).decode(FORMAT)   #Number of bytes it receives, it blocks on this line until it receives
            msgArr = msg.split()
            if msg:
                if msgArr[0] == DISCONNECT_MESSAGE:            #Completely removing all aspects of that client from the server when they diconnect
                    del activeTCPClientsUsername[msgArr[1]]
                    del activeUDPClientsUsername[msgArr[1]]
                    connectionSocket.send("You have disconnected,bye!".encode(FORMAT))
                    print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")
                    connected= False
                elif msg[0:4] == "JOIN":
                    if msgArr[3] in activeTCPClientsUsername:   #If username client tried to enter already exists on the server
                        connectionSocket.send("exists".encode(FORMAT))  #Tell client to re-enter username
                    else:
                        clientInfoArr = msg.split()
                        activeTCPClientsUsername[clientInfoArr[3]] = addr  #Maps the clients username to their TCP port
                        connectionSocket.send("you have successfully joined the server.".encode(FORMAT))
                elif msg == "!list":
                    returnStr = "This is the list of active clients:\n"
                    for key, value in activeUDPClientsUsername.items():
                        if clientStatus[value] == "active":
                            returnStr += (f"{key}: {value}\n")   
                    if returnStr == "This is the list of active clients:\n":
                        connectionSocket.send("There are currently no active users showing up\n".encode(FORMAT))
                    else:
                        connectionSocket.send(returnStr.encode(FORMAT)) 
                elif msg.startswith("!broadcast "): #Broadcasts message to all active clients on the server
                    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as broadcast_socket:
                        for key,value in activeUDPClientsUsername.items():
                            if key != msgArr[1]:
                                ip = value[0]
                                port = int(value[1])
                                chatArr = [msgArr[0],msgArr[1], ' '.join(msgArr[2:])]
                                broadcast_socket.sendto(f"BROADCAST {chatArr[1]} says: {chatArr[2]}".encode(FORMAT),(ip,port))
                            else:  continue
                    connectionSocket.send("Message has been broadcasted to all active clients.".encode(FORMAT))
                elif msg == "!help":
                        connectionSocket.send(help_message.encode(FORMAT))  #Send list of commands to client
                elif msgArr[0] == "!hide":
                    if (clientStatus[(msgArr[1],msgArr[2])] == "hidden"):
                        connectionSocket.send(f"You are already hidden".encode(FORMAT))
                    else:
                        clientStatus[(msgArr[1],msgArr[2])] = "hidden"  #Changing the status of client in dictionary to hidden
                        connectionSocket.send(f"You are now hidden".encode(FORMAT))
                elif msgArr[0] == "!active":
                    if (clientStatus[(msgArr[1],msgArr[2])] == "active"):
                        connectionSocket.send(f"You are already active".encode(FORMAT))
                    else:
                        clientStatus[(msgArr[1],msgArr[2])] = "active"  #Changing the status of client in dictionary to hidden
                        connectionSocket.send(f"You are now active".encode(FORMAT))
                elif msgArr[0] == "UDP":    # [0] is string 'udp', [1] is ip, [2] is port number, [3] is username
                    activeUDPClientsUsername[msgArr[3]] = (msgArr[1],msgArr[2]) #Mapping the clients username to their main UDP socket
                    clientStatus[(msgArr[1],msgArr[2])] = "active"
                    connectionSocket.send((f"Reminder: Your UDP socket is {activeUDPClientsUsername[msgArr[3]]}").encode(FORMAT))
                elif msg in activeUDPClientsUsername:
                    result_string = ' '.join(str(element) for element in activeUDPClientsUsername[msg])    # 192.123.3.8 42598, this returns this string
                    connectionSocket.send(result_string.encode(FORMAT))                                    #This is sending a string with the IP and PORT seperated by a space
                elif msg not in activeUDPClientsUsername:
                    connectionSocket.send((f"command does not exist on the server").encode(FORMAT))
                else:
                    connectionSocket.send((f"Invalid Command: {msg}").encode(FORMAT))
        
        connectionSocket.close()
    except ConnectionResetError:
        print("Connection reset by peer.")
        #shut down the sever safely
        serverSocket.close()
        
    

def start():
    serverSocket.listen(1)    #waits for incoming TCP requests.
    print(f"[LISTENING] server is listening on IP: {SERVER}, Port Number: {PORT}")
    print()
    
    try:
        while True:                 
            connectionSocket, addr = serverSocket.accept()  #Waits for a new connection, addr is storing the IP and port number it came from AND connectionSocket is a socket object which allows us to comunicate back to the socket that connected
            
            thread = threading.Thread(target=handleClient,args=(connectionSocket,addr)) #When a new connection occurs create a new thread to handle it
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")    #Always -1 because of this always True thread
    except  (socket.error, socket.timeout):
        print("Error, server socket has closed")
        
                                                        
print("[STARTING] server is starting...")
start()