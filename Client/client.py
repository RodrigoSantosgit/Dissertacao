''' 
	Rodrigo Santos, n mec 89180
	
	- Dissertation Project
	ECHO CLIENT UDP
'''

import sys
import socket
import time   
import subprocess

def main():

	time.sleep(13)

	remoteClientAddr = "10.30.0.30" # default value
	remport = "5000" # default value
	port = 5001 # default value
	host = 'localhost' # default value
	
	for i in range(1, len(sys.argv),2):
	    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
	        host = sys.argv[i + 1]
	    elif (sys.argv[i] == "--port" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
	        port = int(sys.argv[i + 1])
	    elif (sys.argv[i] == "--remoteport" or sys.argv[i] == "-rp") and i != len(sys.argv) - 1:
	        remport = int(sys.argv[i + 1])
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
	s.bind((host, port))
	
	# connect it to server and port
	# number on local computer.
	log("TRYING TO CONNECT TO: " + remoteClientAddr + ":" + str(remport))
	
	# Message exchange Cycle
	i = 0
	
	time.sleep(2)
	log(" - UDP COMMS - \n")
	s.sendto(b"HELLO SERVER!", (remoteClientAddr, remport))
	log("HELLO SERVER!")
	
	while True:
	    
	    msg = []
	    
	    while not msg:
	    	msg, addr = s.recvfrom(1024)

	    if msg.decode() == "Bye Client":
	    	break

	    if i == 36:
	    	time.sleep(0.5)
	    	send_msg = "Bye Server"
	    	s.sendto(send_msg.encode(), (remoteClientAddr, remport))
	    	log(send_msg)
	    else:
	       time.sleep(0.5)
	       send_msg = "MSG Number = " + str(i)
	       s.sendto(send_msg.encode(), (remoteClientAddr, remport))
	       log(send_msg)
	       i = i + 1

	# disconnect the client and remove file
	s.close()

###############################################
#			LOG			#
###############################################
def log(msg):

	# Building the command.
	command = ['echo', msg]

	subprocess.call(command)

###############################################

if __name__ == "__main__":
	main()
