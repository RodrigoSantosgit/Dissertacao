''' 
	Rodrigo Santos, n mec 89180
	
	- Dissertation Project
	SERVER CODE FOR KUBERNETES SERVICE UDP
'''

import sys
import socket

def main():

	# create a socket at server side
	# using UDP / IP protocol
	conn = socket.socket(socket.AF_INET,
		          socket.SOCK_DGRAM)
	conn.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	# bind the socket with server
	# and port number
	conn.bind(('0.0.0.0', 5000))
	
	## PROCESSING -------
	msg = []

	while True:
		
		while not msg:
			try:
				msg, addr = conn.recvfrom(1024)
			except:
				sys.exit(0)

		if msg.decode() == "Bye Server":
			conn.sendto(b"Bye Client", (addr[0], addr[1]))
		else:
			msg_to_send = "Received: " + msg.decode()
			conn.sendto(msg_to_send.encode(), (addr[0], addr[1]))
		
		msg = []

	# disconnect the server
	conn.close()


###############################################
if __name__ == "__main__":
	main()

