import socket
import os
from subprocess import Popen, PIPE

def main():

	host = 'localhost'
	#host = "10.0.2.15"
	port = 17000
	switch_port = 50001
	#port = 30500

	# create a socket at client side
	# using TCP / IP protocol
	s = socket.socket(socket.AF_INET,
		          socket.SOCK_STREAM)

	s.bind(('localhost', 0))
	hostname = socket.gethostname()
	## getting the IP address using socket.gethostbyname() method
	ip_address = socket.gethostbyname(hostname)
	
	print(f"IP Address: {ip_address}")
	# connect it to server and port
	# number on local computer.
	print("TRYING TO CONNECT TO: " + host + ":" + str(switch_port))
	s.connect((host, switch_port))

	# Message exchange Cycle
	msg = []
	i = 0
	while True:

	    while not msg:	
	    	msg = s.recv(1024)

	    print(msg.decode())

	    if msg.decode() == "Bye Client":
	    	break

	    msg = []

	    send_msg = input("[CLIENT] -> Message to send: ")
	    s.send(send_msg.encode())

	# disconnect the client and remove file
	s.close()


if __name__ == "__main__":
    main()