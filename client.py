import socket
import hashlib



sequencenum = 0
FIN_flag = False

# Define the server address and port
server_address = ('localhost', 5000)



def calculate_checksum(message):
    hasher = hashlib.md5()
    hasher.update(message.encode("utf-8"))
    checksumB=hasher.digest()
    return checksumB.hex()
  
# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send a message to the server
sock.sendto('SYN'.encode(), server_address)
print("Establishing connection...")
data, server_address = sock.recvfrom(1024)

# Establishing the connection

if data.decode() == 'SYN-ACK':
    sequencenum=sequencenum+1
    ACKR='ACK'+';'+str(sequencenum)
    sock.sendto(ACKR.encode(), server_address)
    print('Connection established with', server_address)
    
else:
    print("Connection failied")


while True:
    # Send a message to the server
    msg_in = input("Enter the message:")

    # If FIN, Close the connection
    if msg_in == "FIN":
        FIN_flag=True
        sock.sendto("FIN".encode(), server_address)

        print("SENT : FIN")
        data, address = sock.recvfrom(1024) 
        r_msg=data.decode('utf-8')
        if r_msg=="ACK":
            print("recieved "+r_msg)
            data, address = sock.recvfrom(1024)
            r_msg=data.decode('utf-8')
            if r_msg =="FIN":
                print("recieved "+r_msg)
                sock.sendto("ACK".encode(), server_address)
                break
    if FIN_flag == True:
        exit()
    
    # requests = []
    # with open('test_requests.txt', 'rb') as f:
    #     data = f.read()
    # lines = data.split('%')

    # for line in lines:
    #     if not line:
    #         break
    #     requests.append(line)

    request = f"POST test_2.txt HTTP/1.1\r\nHost: localhost:5000\r\n?islam\r\n"
    msg_in = request
    
    message=msg_in +";"+ str(sequencenum)
    length=len(message)
    message=message + ";" + str(calculate_checksum( message))
    # print(message)

    sock.sendto(message.encode(), server_address)
    # Receive a response from the server
    sock.settimeout(5.0)


    ## Waiting for response (Stop and wait)
    while True:
        try:
            data, address = sock.recvfrom(1024)
            print("No time out")
            break
        except socket.timeout:
            print("Time out sending again")
            sock.sendto(message.encode(), server_address)
            continue

    r_msg=data.decode('utf-8')
    M_ACK,N_ACK,response=r_msg.split(";")
    N_ACK=int(N_ACK)

    if(N_ACK == sequencenum):
        message=msg_in+";"+ str(sequencenum)
        message=message + ";" + str(calculate_checksum( message))
        print('Received {} from {}'.format(data.decode(), address))
        print("resending the message")
        sock.sendto(message.encode(), server_address)
    else:
        print('Received {} from {}'.format(data.decode(), address))
        print("Data recieved sucessfully")
        sequencenum=sequencenum+length


# Closing the connection
sock.close()