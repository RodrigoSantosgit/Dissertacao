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

	time.sleep(7)

	remoteClientAddr = "10.20.0.4" # default
	port = "5000"     #default
	for i in range(1, len(sys.argv),2):
	    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
	        host = sys.argv[i + 1]
	    elif (sys.argv[i] == "--port" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
	        port = int(sys.argv[i + 1])
	    elif (sys.argv[i] == "--remoteClientAddr" or sys.argv[i] == "-rmaddr") and i != len(sys.argv) - 1:
	        remoteClientAddr = sys.argv[i + 1]
	    else:
	        print("Unkown argument", sys.argv[i])
	        quit()

	# create a socket at client side
	# Socket with UDP / IP
	s = socket.socket(socket.AF_INET,
		          socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.bind((host, 5001))
	
	# connect it to server and port
	# number on local computer.
	print("TRYING TO CONNECT TO: " + remoteClientAddr + ":" + str(port))
	
	# Message exchange Cycle
	msg = []
	i = 0
	
	ping(remoteClientAddr)
	
	'''while True:
	    
	    while not msg:
	    	msg, addr = s.recvfrom(1024)

	    print(msg.decode())

	    if msg.decode() == "Bye Client":
	    	break

	    if i == 9:
	    	msg = []
	    	time.sleep(2)
	    	send_msg = "Bye Server"
	    	s.sendto(send_msg.encode(), (remoteClientAddr, port))
	    else:
	       msg = []

	       time.sleep(2)
	       send_msg = "MSG Number = " + str(i)
	       s.sendto(send_msg.encode(), (remoteClientAddr, port))
	       i = i + 1

	# disconnect the client and remove file
	s.close()'''
	
def ping(remoteClientAddr):

	# Option for the number of packets as a function of
	param = '-n' if platform.system().lower()=='windows' else '-c'

	# Building the command.
	command = ['ping', param, '20', remoteClientAddr]

	subprocess.call(command)


if __name__ == "__main__":
	main()
