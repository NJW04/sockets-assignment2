import socket
import threading


def get_local_ip():
    try:
        # Create a socket object and connect to an external server
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except socket.error:
        return "Unable to determine IP address"

PORT = 5051
SERVER = get_local_ip() #Instead of hard coding in the IP Address this gets the IP Address of local machines
#SERVER = "196.24.190.87"
ADDRESS = (SERVER,PORT) #This is the exact address with matching IP and Port number for the server
FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!disconnect"

serverSocket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)   #SOCK_STREAM is needed for TCP server
serverSocket.bind(ADDRESS)

#Array keeping the IP and Port number of all active clients
activeClients = []
clientStatus = {}
activeClientsUsername = {}
activeUDPClientsUsername = {}

help_message = "Available Commands:\n" \
                   "- !help: Display a list of available commands.\n" \
                   "- !list: Display a list of active clients.\n" \
                   "- SEND <recipientUsername> <content>: Send a message to another client.\n" \
                    "- !hide: Hide yourself to not appear to any other client\n" \
                    "- !active: Set yourself as active to be seen by other clients\n" \
                   "- !disconnect: Disconnect from the server.\n"

def handleClient(connectionSocket, addr):
    print(f"[NEW CONNECTION] {addr} connected.")
    activeClients.append(addr)  #Adds a tuple containing clients TCP IP and port number
    connected = True
    try:
        while connected:
            msg = connectionSocket.recv(2048).decode(FORMAT)   #Number of bytes it receives, it blocks on this line until it receives
            msgArr = msg.split()
            if msg:
                if msgArr[0] == DISCONNECT_MESSAGE:
                    if addr in activeClients:
                        activeClients.remove(addr)     #Removing the address from active clients
                    del activeClientsUsername[msgArr[1]]
                    del activeUDPClientsUsername[msgArr[1]]
                    connectionSocket.send("You have disconnected,bye!".encode(FORMAT))
                    print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 2}")
                    connected= False
                elif msg[0:4] == "JOIN":
                    if msgArr[3] in activeUDPClientsUsername:
                        connectionSocket.send("That username already exists".encode(FORMAT))
                    else:
                        clientInfoArr = msg.split()
                        activeClientsUsername[clientInfoArr[3]] = addr  #this is where it maps the clients username to their TCP port
                        connectionSocket.send("you have successfully joined the server".encode(FORMAT))
                elif msg == "!list":
                    returnStr = "This is the list of active clients:\n"
                    for key, value in activeUDPClientsUsername.items():
                        if clientStatus[value] == "active":
                            returnStr += (f"{key}: {value}\n")   
                    connectionSocket.send(returnStr.encode(FORMAT))
                elif msg == "!help":
                        connectionSocket.send(help_message.encode(FORMAT))
                elif msgArr[0] == "!hide":
                    if (clientStatus[(msgArr[1],msgArr[2])] == "hidden"):
                        connectionSocket.send(f"You are already hidden".encode(FORMAT))
                    else:
                        clientStatus[(msgArr[1],msgArr[2])] = "hidden"
                        connectionSocket.send(f"You are now hidden".encode(FORMAT))
                elif msgArr[0] == "!active":
                    if (clientStatus[(msgArr[1],msgArr[2])] == "active"):
                        connectionSocket.send(f"You are already active".encode(FORMAT))
                    else:
                        clientStatus[(msgArr[1],msgArr[2])] = "active"
                        connectionSocket.send(f"You are now active".encode(FORMAT))
                elif msgArr[0] == "UDP":    # 0 is string 'udp', 1 is ip, 2 is port number, 3 is username
                    activeUDPClientsUsername[msgArr[3]] = (msgArr[1],msgArr[2])
                    clientStatus[(msgArr[1],msgArr[2])] = "active"
                    connectionSocket.send((f"\nThe UDP socket for you is {activeUDPClientsUsername[msgArr[3]]}").encode(FORMAT))
                elif msg in activeUDPClientsUsername:
                    result_string = ' '.join(str(element) for element in activeUDPClientsUsername[msg])    # 192.123.3.8 42598, this returns this string
                    connectionSocket.send(result_string.encode(FORMAT)) #This is sending a string with a space of the IP and PORT
                elif msg not in activeUDPClientsUsername:
                    connectionSocket.send("does not exist on the server".encode(FORMAT))
                else:
                    connectionSocket.send((f"Invalid Command: {msg}").encode(FORMAT))
        
        connectionSocket.close()
    except ConnectionResetError:
        print("Connection reset by peer.")
        #shut down the sever safely
        serverSocket.close()
        
    

def start():
    serverSocket.listen(1)    #waits for incoming TCP requests.
    print(f"[LISTENING] server is listening on {SERVER}")
    print()
    
    try:
        while True:                 
            connectionSocket, addr = serverSocket.accept()  #Waits for a new connection, addr is storing the IP and port number it came from AND connectionSocket is a socket object which allows us to comunicate back to the thing that connected
            
            thread = threading.Thread(target=handleClient,args=(connectionSocket,addr)) #When a new connection occurs create a new thread to handle it
            thread.start()
            print(f"[ACTIVE CONNECTIONS] {threading.active_count() - 1}")    #Always -1 because of this always True thread
    except  (socket.error, socket.timeout):
        print("Error error, server socket has closed")
        
                                                        
print("[STARTING] server is starting...")
start()