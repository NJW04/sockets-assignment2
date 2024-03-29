import socket
import threading
import re
import os

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
        client_TCP_socket.send(msg.encode(FORMAT))      #Encoding it to be sent to the server
        
        #View the message sent from server back to client
        print(client_TCP_socket.recv(2048).decode(FORMAT))
    except ConnectionError:
        # Handle the case where the connection fails or the server is unreachable
        print("Connection error: Server not available")
    
def sendToServerReturn(client_TCP_socket,msg):
    client_TCP_socket.send(msg.encode(FORMAT))          #Encoding it to be sent to the server
    return (client_TCP_socket.recv(2048).decode(FORMAT))
    
#This method is used when we get the IP and Port number from the server
def sendToFriend(socket,message,other_client_ip,other_client_port,username):
    friendAddress = (other_client_ip,other_client_port)
    message = username + " " + message + "\nEnter command (use !help): "
    socket.sendto(message.encode(FORMAT), friendAddress)
    
#This method is used when we have to manually enter the IP and Port number
def sendToFriendUDP(socket,message,other_client_ip,other_client_port,your_ip,your_port):
    friendAddress = (other_client_ip,other_client_port)
    message = f"({your_ip},{your_port})" + " " + message + "\n>>(type !help)"
    socket.sendto(message.encode(FORMAT), friendAddress)
    
def receive_messages(sock):
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode(FORMAT)
            messageArr = message.split(' ')
            sender = messageArr[0]                                                  #Seeing what kind of message is being sent and how to interpret it
            messageArr = messageArr[1:]
            message = ' '.join(messageArr)
            if HIDDEN:                                                              #If client is hidden do not print out received method
                continue
            elif HIDDEN == False:
                if sender == "BROADCAST":
                    print(f"\n[{sender}] {message} \nEnter command (use !help):")   #Display it in the correct broadcast format
                else:
                    print(f"\n[{sender} says]: {message}")
    except Exception as e:
        print(f"Error listening for messages: {e}")
    finally:
        pass


def start_client(main_UDP_socket,client_TCP_socket,username):
    udpAddress, udpPort = main_UDP_socket.getsockname()    #Port and ip for udp socket
    
    print(f"\n{username}, you have successfully joined the server")
    sendToServer(client_TCP_socket,f"UDP {udpAddress} {udpPort} {username}")  
    
    #When they join the server they are defaulted to being active until they change it
    global HIDDEN
    HIDDEN = False  
    
    while True:
        msgToSend = input("Enter command (use !help): ")
        print()
        msgToSendArr = msgToSend.split(" ") #['JOIN', '192.168.3.223','5050','Nathan']
        if not msgToSend:
            print("Empty command")
        elif len(msgToSendArr) == 1:
            if msgToSend == DISCONNECT_MESSAGE:
                sendToServer(client_TCP_socket,msgToSend + " " + username)
                HIDDEN = False
                break
            elif msgToSend == "!active" or msgToSend == "!hide":                    #If client wants to change their state on the server, it changes it client side as well
                if msgToSend == "!hide":
                    HIDDEN = True
                if msgToSend == "!active":
                    HIDDEN = False
                msgToSend += " " + udpAddress + " " + str(udpPort)
                sendToServer(client_TCP_socket,msgToSend)
            else:                   
                sendToServer(client_TCP_socket,msgToSend)                           #Only the 1 word commands that the server knows
        else:
            if msgToSendArr[0] == "!broadcast":
                msg = ' '.join(msgToSendArr[1:])
                contentArr = [msgToSendArr[0],username,msg]
                content = ' '.join(map(str, contentArr))
                print(sendToServerReturn(client_TCP_socket,content))                #You send string: !broadcast Nathan Hello Everyone
                continue
            elif msgToSendArr[0] == "!send":
                matches = re.match(r'(\S+)\s+(\S+)\s+(.*)', msgToSend)              #This is used to properly string slice the command, username and then rest of the message accounting for different punctuation marks
                if matches:
                    command = matches.group(1)
                    name = matches.group(2)
                    message = matches.group(3) + '\n'
        
                    other_client_info = sendToServerReturn(client_TCP_socket,name)   #i.e Ben, this is receiving the IP and PORT number
                    if other_client_info == "command does not exist on the server":
                        print(f"Username: {name}, does not exist on the server")
                    else:
                        other_client_info = other_client_info.split()
                        sendToFriend(main_UDP_socket,message,other_client_info[0],int(other_client_info[1]),username)
                else:
                    print(f"invalid command: {msgToSend}")
                

    # Jump back to main menu loop
    mainLoop(main_UDP_socket)


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
                        print("Invalid input. Third word must contain only digits.\n")
                else:
                    print("Invalid input. Second word must be in IP address format.\n")
            else:
                print("Invalid input. First word must be 'JOIN'.\n")
        else:
            print("Invalid input. Please enter a string with exactly 4 words separated by spaces.\n")
            
    return user_input.lstrip()


def connectToServer(main_udp_socket):
    client_TCP_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)    

    clientInfo = joinCommand()
    clientInfoArr = clientInfo.split()                                      #[JOIN],[192.168.3.223],[5050],Nathan
    PORT = int(clientInfoArr[2])
    SERVER = clientInfoArr[1]
    ADDRESS = (SERVER,PORT)

    try:
        client_TCP_socket.connect(ADDRESS)                                  #Client connecting to address of server
        serverResponse = sendToServerReturn(client_TCP_socket,clientInfo)
        while serverResponse == "exists":
            print("That username already exists on the server, please enter a different one.\n")
            clientInfo = joinCommand()
            clientInfoArr = clientInfo.split()
            serverResponse = sendToServerReturn(client_TCP_socket,clientInfo)
                
        start_client(main_udp_socket,client_TCP_socket,clientInfoArr[3])    #Starting the client with their 2 types of sockets and their unique username
    except (socket.error, socket.timeout,ConnectionError) as e:
            print(f"Error: Unable to connect to the server. {e}")

    finally:
            client_TCP_socket.close()
   

def sendThroughUDP():
    udp_socketIP = main_udp_socket.getsockname()[0]
    udp_socketPort = main_udp_socket.getsockname()[1]
    
    IPandPort = input("[Enter these parameters: <recepientIP> <recepientPort>]: ")
    IPandPortArr = IPandPort.split(' ')
    message = input("Now the message you wish to send: ")
    
    #Need to supply and remember recepient IP and Port and sender IP and Port
    sendToFriendUDP(main_udp_socket,message,IPandPortArr[0],int(IPandPortArr[1]),udp_socketIP,udp_socketPort)
    mainLoop(main_udp_socket)

         
def mainLoop(main_UDP_socket):
    global HIDDEN
    HIDDEN = False
    # Start a thread to receive messages instantly
    receive_thread = threading.Thread(target=receive_messages, args=(main_UDP_socket,))
    receive_thread.start()
    print(f"\nYOUR MAIN RECEIVING SOCKET IS {main_udp_socket.getsockname()}\n")
    
    userInput = ""
    print("Welcome to this chat application")
    while userInput != "q":
        userInput = input("1 - Join the server\n2 - Message another client through UDP\nq - Quit Program\n>>").lstrip()
        if userInput == "1":
            connectToServer(main_udp_socket)
        elif userInput == "2":
            sendThroughUDP()
        elif userInput == "!help":
            pass
        elif userInput == "q":
            main_udp_socket.close()
        else:
            print("Invalid Input.")


FORMAT = 'utf-8'
DISCONNECT_MESSAGE = "!disconnect"
#As soon as the client is run make its main UDP socket variable
main_udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
main_udp_socket.bind((get_local_ip(),0))

#Jump to main program loop
mainLoop(main_udp_socket)