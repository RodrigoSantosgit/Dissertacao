''' 
	ECHO CLIENT UDP
'''

import sys
import socket
import os
import time
import logging
import platform   
import subprocess

def main():

	time.sleep(20)

	host = "10.4.0.4"
	port = "5000"
	for i in range(1, len(sys.argv),2):
	    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
	        host = sys.argv[i + 1]
	    elif (sys.argv[i] == "--port" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
	        port = int(sys.argv[i + 1])
	    else:
	        print("Unkown argument", sys.argv[i])
	        quit()

	# create a socket at client side

	# Socket with UDP / IP
	s = socket.socket(socket.AF_INET,
		          socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.bind(('10.3.0.3', 5001))
	hostname = socket.gethostname()
	## getting the IP address using socket.gethostbyname() method
	ip_address = socket.gethostbyname(hostname)

	#logging.info(f"IP Address: {ip_address}")
	print(f"IP Address: {ip_address}")
	# connect it to server and port
	# number on local computer.
	#logging.info("TRYING TO CONNECT TO: " + host + ":" + str(port))
	print("TRYING TO CONNECT TO: " + host + ":" + str(port))

	# Message exchange Cycle
	msg = []
	lastmsg = ' '
	i = 0
	
	ping(host)
	
	while True:

	    timest = time.time()
	    
	    while not msg:	
	    	msg, addr = s.recvfrom(1024)

	    #print(msg)
	    #logging.info(msg.decode())
	    print(msg.decode())

	    if msg.decode() == "Bye Client":
	    	break

	    if i == 9:
	    	msg = []
	    	time.sleep(2)
	    	send_msg = "Bye Server"
	    	s.sendto(send_msg.encode(), (host, port))
	    	lastmsg = send_msg
	    else:
	       msg = []

	       time.sleep(2)
	       #send_msg = input("[CLIENT] -> Message to send: ")
	       send_msg = "MSG Number = " + str(i)
	       s.sendto(send_msg.encode(), (host, port))
	       lastmsg = send_msg
	       i = i + 1

	# disconnect the client and remove file
	s.close()
	
def ping(host):

	# Option for the number of packets as a function of
	param = '-n' if platform.system().lower()=='windows' else '-c'

	# Building the command.
	command = ['ping', param, '1', host]

	subprocess.call(command)


if __name__ == "__main__":
	main()
