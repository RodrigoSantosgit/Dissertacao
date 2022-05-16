import socket
import os
from subprocess import Popen, PIPE
import time

def main():

	#host = "localhost"
	#host = "10.0.2.15"
	host = "172.17.0.2"
	#port = 50001
	#port = 30500
	port =  5000

	# create a socket at client side
	# using TCP / IP protocol
	s = socket.socket(socket.AF_INET,
		          socket.SOCK_STREAM)

	#s.bind(('10.0.3.15', 0))
	hostname = socket.gethostname()
	## getting the IP address using socket.gethostbyname() method
	ip_address = socket.gethostbyname(hostname)
	
	print(f"IP Address: {ip_address}")
	# connect it to server and port
	# number on local computer.
	print("TRYING TO CONNECT TO: " + host + ":" + str(port))
	s.connect((host, port))

	# Message exchange Cycle
	msg = []
	i = 0
	while True:

	    while not msg:	
	    	msg = s.recv(1024)

	    print(msg.decode())

	    if msg.decode() == "Bye Client":
	    	break

	    if i == 9:
	    	msg = []
	    	time.sleep(5)
	    	send_msg = "Bye Server"
	    	s.send(send_msg.encode())
	    else:
	       msg = []

	       time.sleep(5)
	       #send_msg = input("[CLIENT] -> Message to send: ")
	       send_msg = "MSG Number = " + str(i)
	       s.send(send_msg.encode())
	       i = i + 1

	# disconnect the client and remove file
	s.close()


if __name__ == "__main__":
    main()
