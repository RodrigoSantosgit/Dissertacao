''' 
	SERVER ACTING AS CLIENT FOR P4SWITCH UDP
'''

import sys
import socket
import logging
import time
import platform   
import subprocess
import requests

def main():

	time.sleep(10)
	
	host = 'localhost' #default
	remoteClientAddr = "10.13.0.3" # default
	port = "5001" # default
	for i in range(1, len(sys.argv),2):
	    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
	        host = sys.argv[i + 1]
	    elif (sys.argv[i] == "--port" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
	        port = int(sys.argv[i + 1])
	    elif (sys.argv[i] == "--remoteClientAddr" or sys.argv[i] == "-rmaddr") and i != len(sys.argv) - 1:
	        remoteClientAddr = sys.argv[i + 1]
	    elif (sys.argv[i] == "--mode" or sys.argv[i] == "-m") and i != len(sys.argv) - 1:
	        mode = sys.argv[i + 1]
	        if mode != "rightaway" and mode != "trigger":
	            print("[ERROR] Unknown Mode of operation: " + mode +"\n Modes available are: rightaway trigger\n")
	            quit()
	    else:
	        print("[ERROR] Unknown argument: " + sys.argv[i] + "\n")
	        quit()

	# Instantiate k8s deployment
	if mode == "rightaway":
	    response = requests.put("http://10.30.0.50:8000/instantiateService?namespace=default&name=server-udp&app=server-udp&container_name=server-udp&image=server-clientlike-udp%3Alatest")
	    print(response)
	    #response = requests.put("http://10.16.3.20:8000/create-service?namespace=default&name=server-udp&protocol=UDP&port=5000&targetPort=44000")
	    #print(response)
	    
	# Show deployement on the k8s cluster
	#response = requests.get("http://10.4.0.20:8000/get-pods")
	#print(response)

	# take the server name and port name
	serv_port = 5000

	# create a socket at server side
	# using UDP / IP protocol
	conn = socket.socket(socket.AF_INET,
		          socket.SOCK_DGRAM)
	conn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	# bind the socket with server
	# and port number
	conn.bind((host, serv_port))

	# allow maximum 1 connection to
	# the socket
	#conn.listen(1)

	# wait till a client accept
	# connection
	#conn, addr = conn.accept()

	# display client address
	#print("CONNECTION FROM:", str(addr))

	# connect it to server and port
	# number on local computer.
	print("TRYING TO CONNECT TO: " + remoteClientAddr + ":" + str(port))
	
	ping(remoteClientAddr)
	time.sleep(10)

	# send message to the client after
	# encoding into binary string
	msg = []
	
	'''conn.sendto(b"[SERVER] -> HELLO CLIENTS!", (remoteClientAddr, port))

	while True:
		
		while not msg:
			msg, addr = conn.recvfrom(1024)

		print(msg.decode())

		if msg.decode() == "Bye Server":
			conn.sendto(b"Bye Client", (remoteClientAddr, port))
			break
		else:
			msg_to_send = "[SERVER] -> Received: " + msg.decode()
			conn.sendto(msg_to_send.encode(), (remoteClientAddr, port))
		
		msg = []

	# disconnect the server
	conn.close()'''
	
	# Delete k8s deployment instantiated in rightaway mode
	if mode == "rightaway":
	    response = requests.delete("http://10.30.0.50:8000/deleteService?name=server-udp")
	    print(response)
	    #response = requests.get("http://10.16.3.20:8000/delete-service?name=server-udp")
	    #print(response)
	
def ping(remoteClientAddr):

	# Option for the number of packets as a function of
	param = '-n' if platform.system().lower()=='windows' else '-c'

	# Building the command.
	command = ['ping', param, '20', remoteClientAddr]

	subprocess.call(command)

if __name__ == "__main__":
	main()
