import socket

# take the server name and port name
host = 'localhost'
port = 5000

# create a socket at server side
# using TCP / IP protocol
s = socket.socket(socket.AF_INET,
                  socket.SOCK_STREAM)

# bind the socket with server
# and port number
s.bind(('', port))

# allow maximum 1 connection to
# the socket
s.listen(1)

# wait till a client accept
# connection
conn, addr = s.accept()

# display client address
print("CONNECTION FROM:", str(addr))

# send message to the client after
# encoding into binary string
msg = []

conn.send(b"[SERVER] -> HELLO CLIENTS!")

while True:
	
	while not msg:
		msg = conn.recv(1024)

	if msg.decode() == "Bye Server":
		conn.send(b"Bye Client")
		conn, addr = s.accept()
		conn.send(b"[SERVER] -> Hello Client!")
	else:
		msg_to_send = "[SERVER] -> Received: " + msg.decode()
		conn.send(msg_to_send.encode())
	
	msg = []

# disconnect the server
s.close()
