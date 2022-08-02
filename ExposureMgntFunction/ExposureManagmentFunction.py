'''
	Rodrigo Santos, nº mec 89180
		
	  - Dissertation Project
	Exposure Managment Function
'''

from fastapi import FastAPI
from kafka import KafkaProducer

app = FastAPI()
global producer

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
		msg = '[COMPUTATIONCONTROLLER] [INSTANTIATE] ' + namespace + ' ' + name + ' ' + app + ' ' + container_name + ' ' + image
		producer.send('ComputationManagment', msg.encode())
	except:
		print('\n[ERROR] Something went wrong!\n')
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
		msg = '[COMPUTATIONCONTROLLER] [DELETE] ' + namespace + ' ' + name
		producer.send('ComputationManagment', msg.encode())
	except:
		print('\n[ERROR] Something went wrong!\n')
		return {"ERROR"}

	return {"SUCCESS"}

