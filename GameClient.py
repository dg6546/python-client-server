#3035239404
#Lee Ming Tsun
#8/Mar/2020

import socket
import os.path
import sys

def main(argv):
    # create socket and connect to server
    serverName = argv[1]
    serverPort = int(argv[2])
    try:
        clientSocket = socket.socket()
        clientSocket.connect( (serverName, serverPort) )
        clientSocket.setblocking(1)
    except socket.error as emsg:
        print("Socket error: ", emsg)
        sys.exit(1)
    # once the connection is set up; print out 
    # the socket address of your local socket
    #print("Connection established. My socket address is", clientSocket.getsockname())
    authed = False
    while not authed: # loop until login correctly
        username = input("Please input your user name: ")
        password = input("Please input your password: ")
        msg = "/login " + username + ' ' + password
        clientSocket.send(msg.encode())
        rmsg = ''
        rmsg = clientSocket.recv(1024)
        rmsgDecoded = rmsg.decode()
        print(rmsgDecoded)
        responseCode, *content = rmsgDecoded.split(" ")
        if responseCode == "1001": #successfully login
            authed = True
    userExit = False
    while not userExit: # main communication with server
        msg = input("")
        try:
            clientSocket.send(msg.encode())
            rmsg = clientSocket.recv(1024)
        except socket.error as e:
            print(f"Server disconnect because {e}")
            break
        rmsgDecoded = rmsg.decode()
        print(rmsgDecoded)
        responseCode, *content = rmsgDecoded.split(" ")
        if responseCode == "4001":
            userExit = True
        if responseCode == "3011": # wait for 3012 from server
            while True:
                rmsg = clientSocket.recv(1024)
                rmsgDecoded = rmsg.decode()
                if rmsgDecoded:
                    print(rmsgDecoded)
                    break
	# close connection
    print("Client ends")
    clientSocket.close()

#driver code
if __name__ == '__main__':
	if len(sys.argv) != 3:
		print("Usage: python3 GameClient.py <Server_addr> <Server_port>")
		sys.exit(1)
	main(sys.argv)