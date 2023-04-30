import socket
import hashlib
import time


HTTP_METHODS = ['GET', 'POST']


def isHTTP(request):
    if ("HTTP") in request:
        return True
    return False

def handle_http_request(sock, addr, request):
    """
    Handle an incoming HTTP request by parsing it, processing it, and sending a response.
    """
    if not isHTTP(request):
        message = 'ACK; '+str(ACKnum)+'; '+request
        sock.sendto(message.encode(), addr)
        return
    
    method, headers, body = parse_http_request(request)
    if method not in HTTP_METHODS:
        response = build_http_response('405 Method Not Allowed', {}, '')
    elif method == 'GET':
        try:
            with open(headers['filename'], 'rb') as f:
                data = f.read()
                headers['Content-Length'] = len(data)
                response = build_http_response('200 OK', headers, data)
        except FileNotFoundError:
            response = build_http_response('404 Not Found', {}, '')
    elif method == 'POST':
        try:
            with open(headers['filename'], 'wb') as f:
                f.write(body.encode())
            response = build_http_response('200 OK', {}, '')
        except Exception:
            response = build_http_response('500 Internal Server Error', {}, '')
    else:
        response = build_http_response('501 Not Implemented', {}, '')
        sock.sendto(response, addr)

    message = 'ACK; '+str(ACKnum)+'; '+response.decode('utf-8')
    sock.sendto(message.encode(), addr)


def parse_http_request(request):
    """
    Parse an HTTP request and return the method, headers, and body as a tuple.
    """
    lines = request.split('\r\n')
    method, path, version = lines[0].split(' ')
    headers = {}
    headers['filename'] = path
    headers['version'] = version
    for line in lines[1:]:
        if not line or line[0] == '?':
            break
        name, value = line.split(': ')
        headers[name.lower()] = value
    body = line[1:]

    return method.upper(), headers, body

def build_http_response(status, headers, body):
    """
    Build an HTTP response with the given status, headers, and body.
    """
    status_line = f"HTTP/1.1 {status}\r\n"
    header_lines = [f"{name}: {value}\r\n" for name, value in headers.items()]
    response = status_line + ''.join(header_lines) + '\r\n' + str(body)
    return response.encode()
    


# Define the server address and port
server_address = ('localhost', 5000)
ACKnum = 0

def calculate_checksum(message):
    hasher = hashlib.md5()
    hasher.update(message.encode("utf-8"))
    checksumB=hasher.digest()
    return checksumB.hex()
  

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the server address and port
sock.bind(server_address)

# Receive data from the client
data, client_address = sock.recvfrom(1024)

# Perform three-way handshake
if data.decode() == 'SYN':
    sock.sendto('SYN-ACK'.encode(), client_address)
    data, client_address = sock.recvfrom(1024)
    data = data.decode('utf-8')
    message ,r_sequence, =data.split(";")
    if message == 'ACK':
        ACKnum=r_sequence
        print('Connection established with', client_address)

print('Server is listening...')

while True:
    # Receive data from the client
    data, address = sock.recvfrom(1024)
    data = data.decode('utf-8')
    # print(data)

    # Handle closing the connection
    if data =="FIN":
        sock.sendto("ACK".encode(), server_address)
        time.sleep(1)
        sock.sendto("FIN".encode(), server_address)
        data, address = sock.recvfrom(1024)
        data = data.decode('utf-8')
        if data == "ACK":
            break
    
    message ,r_sequence,checksum =data.split(";")
    # print(message)

    cal_checksum=message+";"+r_sequence
    cal_checksum=str(calculate_checksum(cal_checksum))

    ## Checking corruption
    if cal_checksum != checksum:
        ACKnum=r_sequence
        message = 'ACK: '+str(ACKnum)
        sock.sendto(message.encode(), address)
        print(" The checksum incorrect")
    else: 
        print('the sequence number  {} from {} and the message {} and the checksum {}'.format(r_sequence, address,message,checksum))
        ACKnum=int(r_sequence)+len(message+"message;"+str(r_sequence))
        handle_http_request(sock, address,message)  



print("CONNECTION ENDED")