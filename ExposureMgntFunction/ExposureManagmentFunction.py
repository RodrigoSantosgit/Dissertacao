'''
	Rodrigo Santos, nº mec 89180
		
	  - Dissertation Project
	Exposure Managment Function
'''

from fastapi import FastAPI
from kafka import KafkaProducer  
import subprocess
import time

app = FastAPI()

global producer
global storage

storage = {}
producer = KafkaProducer(bootstrap_servers='10.0.2.15:9092')

global f

f = open("/tmp/Teste0.txt", "w")
f.write("SYSTEM TEST TIMESTAMPS \n")
f.close()

###############################################
#		Instantiate Service		#
###############################################
@app.put("/instantiateService")
def instantiateService(namespace="default", name="None", app="None", container_name="None", image="None"):

	global producer

	if name=="None" or app=="None" or container_name=="None" or image=="None":
		return {"ERROR"}
	
	try:
		msg = '[COMPUTATIONCONTROLLER] [INSTANTIATE] [RIGHTAWAY] ' + namespace + ' ' + name + ' ' + app + ' ' + container_name + ' ' + image
		producer.send('ComputationManagment', msg.encode())
	except:
		log('\n[ERROR] Something went wrong!\n')
		return {"ERROR"}

	f = open("/tmp/Teste0.txt", "a")
	f.write("KAFKA INST MESSAGE Ts: " + str(time.time())+"\n")
	f.close()

	return {"SUCCESS"}


###############################################
#		Delete Service			#
###############################################
@app.delete("/deleteService")
def deleteService(namespace="default", name="None"):

	global producer
	
	if name == "None":
		return {"ERROR"}

	try:
		msg = '[COMPUTATIONCONTROLLER] [DELETE] [RIGHTAWAY] ' + namespace + ' ' + name
		producer.send('ComputationManagment', msg.encode())
	except:
		log('\n[ERROR] Something went wrong!\n')
		return {"ERROR"}
		
	f = open("/tmp/Teste0.txt", "a")
	f.write("KAFKA DEL MESSAGE Ts: " + str(time.time())+"\n")
	f.close()

	return {"SUCCESS"}


###############################################
#	Instantiate Service Trigger Based	#
###############################################
@app.put("/instantiateTriggerBasedService")
def instantiateTriggerBasedService(namespace="default", name="None", app="None", container_name="None", image="None", max_flows: int = 0, ipaddr="None", protoc="None", port="None"):

	global producer
	global storage

	if name=="None" or app=="None" or container_name=="None" or image=="None" or max_flows == 0 or ipaddr=="None" or protoc=="None" or port=="None":
		return {"ERROR"}
		
	storage[name] = [namespace, name, app, container_name, image, max_flows, ipaddr, protoc, port]

	try:
		msg = '[NETCONTROLLER] [INSTANTIATE] [FLOWCOUNTER] ' + name + ' ' + str(max_flows) + ' ' + ipaddr + ' ' + protoc + ' ' + port
		producer.send('NetManagment', msg.encode())
	except:
		log('\n[ERROR] Something went wrong!\n')
		return {"ERROR"}
		
	f = open("/tmp/Teste0.txt", "a")
	f.write("KAFKA FLOW COUNTER MESSAGE Ts: " + str(time.time())+"\n")
	f.close()

	return {"SUCCESS"}
	
###############################################
#	Delete Service Trigger Based		#
###############################################
@app.delete("/deleteTriggerBasedService")
def deleteTriggerBasedService(name="None"):

	global producer
	global storage

	if name=="None":
		return {"ERROR"}
		
	info = storage.get(name)

	try:
		msg = '[NETCONTROLLER] [DELETE] [FLOWCOUNTER] ' + name + ' ' + str(info[5]) + ' ' + info[6] + ' ' + info[7] + ' ' + info[8]
		producer.send('NetManagment', msg.encode())
	except:
		log('\n[ERROR] Something went wrong!\n')
		return {"ERROR"}
		
	f = open("/tmp/Teste0.txt", "a")
	f.write("KAFKA FLOW COUNTER DEL MESSAGE Ts: " + str(time.time())+"\n")
	f.close()

	return {"SUCCESS"}
	

###############################################
#		FETCH INFO			#
###############################################
@app.get("/fetchInfo")
def fetchInfo(service = 'None'):

	global storage

	if service == 'None':
		return {"ERROR"}
		
	info = storage.get(service)

	return info

###############################################
#			LOG			#
###############################################
def log(msg):

	# Building the command.
	command = ['echo', msg]

	subprocess.call(command)

