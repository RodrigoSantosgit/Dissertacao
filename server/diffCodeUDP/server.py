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

	time.sleep(25)

	host = "10.3.0.3"
	port = "5001"
	for i in range(1, len(sys.argv),2):
	    if (sys.argv[i] == "--host" or sys.argv[i] == "-h") and i != len(sys.argv) - 1:
	        host = sys.argv[i + 1]
	    elif (sys.argv[i] == "--port" or sys.argv[i] == "-p") and i != len(sys.argv) - 1:
	        port = int(sys.argv[i + 1])
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
	    response = requests.put("http://10.4.0.20:8000/create-deployment?namespace=default&name=server-udp&app=server-udp&container_name=server-udp&image=server-clientlike-udp%3Alatest")
	    print(response)
	    
	# Show deployement on the k8s cluster
	#response = requests.get("http://10.4.0.20:8000/get-pods")
	#print(response)

	# take the server name and port name
	#host = 'localhost'
	serv_port = 5000

	# create a socket at server side
	# using UDP / IP protocol
	conn = socket.socket(socket.AF_INET,
		          socket.SOCK_DGRAM)
	conn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	# bind the socket with server
	# and port number
	conn.bind(('10.4.0.4', serv_port))

	# allow maximum 1 connection to
	# the socket
	#s.listen(1)

	# wait till a client accept
	# connection
	#conn, addr = s.accept()

	# display client address
	#print("CONNECTION FROM:", str(addr))

	# SERVER ACTING AS CLIENT FOR P4SWITCH
	#host = "10.5.0.2"
	#port = 9559
	#port = 50002
	#port = 5001
	hostname = socket.gethostname()
	# getting the IP address using socket.gethostbyname() method
	ip_address = socket.gethostbyname(hostname)

	#logging.info(f"IP Address: {ip_address}")	
	print(f"IP Address: {ip_address}")
	# connect it to server and port
	# number on local computer.
	#logging.info("TRYING TO CONNECT TO: " + host + ":" + str(port))
	print("TRYING TO CONNECT TO: " + host + ":" + str(port))
	
	ping(host)

	# send message to the client after
	# encoding into binary string
	msg = []
	
	conn.sendto(b"[SERVER] -> HELLO CLIENTS!", (host, port))
	lastmsg = '[SERVER] -> HELLO CLIENTS!'

	while True:
		
		timest = time.time()
		
		while not msg:
			msg, addr = conn.recvfrom(1024)

		#logging.info(msg.decode())
		print(msg.decode())

		if msg.decode() == "Bye Server":
			conn.sendto(b"Bye Client", (host, port))
			lastmsg = msg_to_send
			#conn, addr = s.accept()
			#conn.send(b"[SERVER] -> Hello Client!")
			break
		else:
			msg_to_send = "[SERVER] -> Received: " + msg.decode()
			conn.sendto(msg_to_send.encode(), (host, port))
			lastmsg = msg_to_send
		
		msg = []

	# disconnect the server
	conn.close()
	
	# Delete k8s deployment instantiated in rightaway mode
	if mode == "rightaway":
	    response = requests.get("http://10.4.0.20:8000/delete-deployment?name=server-udp")
	    print(response)
	
def ping(host):

	# Option for the number of packets as a function of
	param = '-n' if platform.system().lower()=='windows' else '-c'

	# Building the command.
	command = ['ping', param, '1', host]

	subprocess.call(command)

if __name__ == "__main__":
	main()
