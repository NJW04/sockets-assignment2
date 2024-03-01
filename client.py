import socket
import threading
import re
import os

FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!disconnect"

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

def sendToServer(client_TCP_socket,msg):
    try:
        msg = msg.lstrip()
        client_TCP_socket.send(msg.encode(FORMAT))    #Encoding it to be sent to the server
        
        #Now to view the message sent from server back to client use
        print(client_TCP_socket.recv(2048).decode(FORMAT))
    except ConnectionError:
        # Handle the case where the connection fails or the server is unreachable
        print("Connection error: Server not available")
    
def sendToServerReturn(client_TCP_socket,msg):
    client_TCP_socket.send(msg.encode(FORMAT))    #Encoding it to be sent to the server
    return (client_TCP_socket.recv(2048).decode(FORMAT))
    
def sendToFriend(socket,message,other_client_ip,other_client_port,username):
    friendAddress = (other_client_ip,other_client_port)
    message = username + " " + message
    socket.sendto(message.encode(FORMAT), friendAddress)
    
def sendToFriend(socket,message,other_client_ip,other_client_port,your_ip,your_port):
    friendAddress = (other_client_ip,other_client_port)
    message = f"({friendAddress[0]},{friendAddress[1]})" + " " + message
    socket.sendto(message.encode(FORMAT), friendAddress)
    

def receive_messages(sock):
    while True:
        try:
            data, addr = sock.recvfrom(1024)
            data = data.decode(FORMAT)
            dataArr = data.split(' ')
            sender = dataArr[0]
            dataArr = dataArr[1:]
            message = ' '.join(dataArr)
            print(f"\n{sender} says: {message}\nEnter command (use !help): ")
        except socket.error:
            break

def start_client(client_TCP_socket,username):
    # Create a UDP socket
    client_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #client_udp_socket.bind(('196.24.189.216',0))
    client_udp_socket.bind((get_local_ip(),0))
    udpAddress, udpPort = client_udp_socket.getsockname()    #Different port and ip for udp socket
    
    print(f"\n{username}, you have successfully joined the server")
    sendToServer(client_TCP_socket,f"UDP {udpAddress} {udpPort} {username}")  
    

    # Start a thread to receive messages
    receive_thread = threading.Thread(target=receive_messages, args=(client_udp_socket,))
    receive_thread.start()
    
    while True:
        msgToSend = input("Enter command (use !help): ")
        print()
        msgToSendArr = msgToSend.split(" ") #['SEND', 'Nathan','Hi,','howsit'] ["!hide"]
        if not msgToSend:
            print("Empty commnad")
        elif len(msgToSendArr) == 1:
            if msgToSend == DISCONNECT_MESSAGE:
                sendToServer(client_TCP_socket,msgToSend + " " + username)
                
                break
            elif msgToSend == "!active" or msgToSend == "!hide":
                msgToSend += " " + udpAddress + " " + str(udpPort)
                sendToServer(client_TCP_socket,msgToSend)
            else:                   
                sendToServer(client_TCP_socket,msgToSend)     #Only the 1 word commands that the server knows
        else:
            if msgToSendArr[0] == "SEND":    #add more protection here
                matches = re.match(r'(\S+)\s+(\S+)\s+(.*)', msgToSend)
                if matches:
                    command = matches.group(1)
                    name = matches.group(2)
                    message = matches.group(3) + '\n'
        
                    other_client_info = sendToServerReturn(client_TCP_socket,name)   #i.e Ben, this is receiving the IP and PORT number
                    if other_client_info == "does not exist on the server":
                        print(f"Username: {name}, does not exist on the server")
                    else:
                        other_client_info = other_client_info.split()
                        sendToFriend(client_udp_socket,message,other_client_info[0],int(other_client_info[1]),username)
                else:
                    print(f"invalid command: {msgToSend}")
                

    # Close the socket.
    client_udp_socket.close()
    mainLoop()


def joinCommand():
    while True:
        user_input = input("[Enter this command to join the server: JOIN <ip> <port> <username>]: ")

        # Split the input into words
        words = user_input.split()

        # Check if the input has exactly 4 words
        if len(words) == 4:
            # Check the first word is "JOIN"
            if words[0] == "JOIN":
                # Check the second word is in IP address format
                if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', words[1]):
                    # Check the third word contains only digits
                    if words[2].isdigit():
                        break
                    else:
                        print("Invalid input. Third word must contain only digits.")
                else:
                    print("Invalid input. Second word must be in IP address format.")
            else:
                print("Invalid input. First word must be 'JOIN'.")
        else:
            print("Invalid input. Please enter a string with exactly 4 words separated by spaces.")
            
    return user_input.lstrip()


def connectToServer():
    client_TCP_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    

    clientInfo = joinCommand()
    clientInfoArr = clientInfo.split()   #[JOIN],[123.123.4.5],[5050],Nathan
    PORT = int(clientInfoArr[2])
    SERVER = clientInfoArr[1]
    ADDRESS = (SERVER,PORT)

    try:
        client_TCP_socket.connect(ADDRESS) #Client connecting to address of server
        serverResponse = sendToServerReturn(client_TCP_socket,clientInfo)
        while serverResponse == "already exists":
            print("Already Exists")
            clientInfo = joinCommand()
            clientInfoArr = clientInfo.split()
            serverResponse = sendToServerReturn(client_TCP_socket,clientInfo)
                
        start_client(client_TCP_socket,clientInfoArr[3])
    except (socket.error, socket.timeout,ConnectionError) as e:
            print(f"Error: Unable to connect to the server. {e}")

    finally:
            client_TCP_socket.close()
   

def sendThroughUDP():
    solo_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    solo_udp_socket.bind((get_local_ip(),0))
    solo_udp_socketIP = solo_udp_socket.getsockname()[0]
    solo_udp_socketPort = solo_udp_socket.getsockname()[1]
    IPandPort = input("[Enter these parameters: <recepientIP> <recepientPort>]: ")
    IPandPortArr = IPandPort.split(' ')
    message = input("Now the message you wish to send: ")
    
    sendToFriend(solo_udp_socket,message,IPandPortArr[0],int(IPandPortArr[1]),solo_udp_socketIP,solo_udp_socketPort)
    solo_udp_socket.close()
    mainLoop()
    

         
def mainLoop():
    userInput = ""
    print("Welcome to this chat application")
    while userInput != "q":
        userInput = input("1 - Join the server\n2 - Message another client through UDP\n")
        if userInput == "1":
            connectToServer()
        elif userInput == "2":
            sendThroughUDP()
        else:
            print("Invalid Input.")


mainLoop()