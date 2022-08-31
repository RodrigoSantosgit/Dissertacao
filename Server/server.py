''' 
	Rodrigo Santos, n mec 89180
	
	- Dissertation Project
	SERVER ACTING AS CLIENT FOR P4SWITCH UDP
'''

import sys
import socket
import time
import platform   
import subprocess
import requests

def main():

	time.sleep(10)
	
	host = 'localhost' #default
	name = '' # default
	image = '' # default
	max_flows = '' # default
	min_flows = '' # default
	expMangFunc = '10.33.0.50' # default
	serv_port = 5000 # default

	## ARGUMENT CHECKING -------
	for i in range(1, len(sys.argv),2):
	    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
	        host = sys.argv[i + 1]
	    elif (sys.argv[i] == "--port" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
	        serv_port = int(sys.argv[i + 1])
	    elif (sys.argv[i] == "--mode" or sys.argv[i] == "-m") and i != len(sys.argv) - 1:
	        mode = sys.argv[i + 1]
	        if mode != "rightaway" and mode != "triggerbased":
	            print("[ERROR] Unknown Mode of operation: " + mode +"\n Modes available are: rightaway triggerbased\n")
	            quit()
	    elif (sys.argv[i] == "--expMangFunc" or sys.argv[i] == "-emf") and i != len(sys.argv) - 1:
	        expMangFunc = sys.argv[i + 1]
	    elif (sys.argv[i] == "--name" or sys.argv[i] == "-n") and i != len(sys.argv) - 1:
	        name = sys.argv[i + 1]
	    elif (sys.argv[i] == "--image" or sys.argv[i] == "-i") and i != len(sys.argv) - 1:
	        image = sys.argv[i + 1]
	    elif (sys.argv[i] == "--maxflows") and i != len(sys.argv) - 1:
	        max_flows = sys.argv[i + 1]
	    elif (sys.argv[i] == "--minflows") and i != len(sys.argv) - 1:
	        min_flows = sys.argv[i + 1]
	    else:
	        print("[ERROR] Unknown argument: " + sys.argv[i] + "\n")
	        quit()
	
	
	## INITIALIZATIONS -------
	# Instantiate k8s deployment rightaway
	if mode == "rightaway":
	    response = requests.put("http://" + expMangFunc + ":8000/instantiateService?namespace=default&name="+name+"&app="+name+"&container_name="+name+"&image="+image)
	# Instantiate Trigger for service instantiate
	if mode == "triggerbased":
	    response = requests.put("http://"+expMangFunc+":8000/instantiateTriggerBasedService?namespace=default&name="+name+"&app="+name+"&container_name="+name+"&image="+image+"&max_flows="+max_flows+"&min_flows="+min_flows)
	

	# create a socket at server side
	# using UDP / IP protocol
	conn = socket.socket(socket.AF_INET,
		          socket.SOCK_DGRAM)
	conn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	# bind the socket with server
	# and port number
	conn.bind((host, serv_port))
	
	conn.settimeout(10)
	
	## PROCESSING -------
	time.sleep(2)

	# send message to the client after
	# encoding into binary string
	msg = []
	log(" - UDP COMMS - ")

	while True:
		
		while not msg:
			try:
				msg, addr = conn.recvfrom(1024)
			except:
				log("Exiting")
				sys.exit(0)

		if msg.decode() == "Bye Server":
			conn.sendto(b"Bye Client", (addr[0], addr[1]))
			log("Bye Client")
		else:
			msg_to_send = "Received: " + msg.decode()
			conn.sendto(msg_to_send.encode(), (addr[0], addr[1]))
			log(msg_to_send)
		
		msg = []

	# disconnect the server
	conn.close()
	
	# Delete k8s deployment instantiated in rightaway mode
	if mode == "rightaway":
	    response = requests.delete("http://" + expMangFunc +":8000/deleteService?name="+name)


###############################################
def ping(remoteClientAddr):

	# Option for the number of packets as a function of
	param = '-n' if platform.system().lower()=='windows' else '-c'

	# Building the command.
	command = ['ping', param, '1', remoteClientAddr]

	subprocess.call(command)


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

