'''
	Rodrigo Santos, nº mec 89180
		
	  - Dissertation Project
	Exposure Managment Function
'''

from fastapi import FastAPI
from kafka import KafkaProducer  
import subprocess

app = FastAPI()

global producer
global storage

storage = {}
producer = KafkaProducer(bootstrap_servers='10.0.2.15:9092')

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

	return {"SUCCESS"}


###############################################
#	Instantiate Service Trigger Based	#
###############################################
@app.put("/instantiateTriggerBasedService")
def instantiateTriggerBasedService(namespace="default", name="None", app="None", container_name="None", image="None", port: int = 1, max_flows: int = 0, min_flows: int = 0):

	global producer
	global storage

	if name=="None" or app=="None" or container_name=="None" or image=="None" or max_flows == 0 or min_flows == 0:
		return {"ERROR"}
		
	storage[port] = [namespace, name, app, container_name, image]

	try:
		msg = '[NETCONTROLLER] [INSTANTIATE] [FLOWCOUNTER] '+ str(port) + ' ' + str(max_flows) + ' ' + str(min_flows)
		producer.send('NetManagment', msg.encode())
	except:
		log('\n[ERROR] Something went wrong!\n')
		return {"ERROR"}

	return {"SUCCESS"}
	

###############################################
#		FETCH INFO			#
###############################################
@app.get("/fetchInfo")
def fetchInfo(port: int = 0):

	global storage

	if port == 0:
		return {"ERROR"}
		
	info = storage.get(port)

	return info

###############################################
#			LOG			#
###############################################
def log(msg):

	# Building the command.
	command = ['echo', msg]

	subprocess.call(command)

