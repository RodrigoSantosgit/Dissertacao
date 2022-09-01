'''
	Rodrigo Santos, n mec 89180
	
	- Dissertation Project
	Network Controller - P4Switch Controller
'''

import argparse
import os
import sys
from time import sleep
from kafka import KafkaConsumer
from kafka import KafkaProducer
import subprocess
import json

import grpc

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
import p4runtime_sh.shell as sh
import p4runtime_lib.helper

global CPU_PORT
global consumer
global producer
global readCounterEnabled
global port_FlowMapping
global ask_inst
global ask_del

CPU_PORT = '510'

ask_del = 0
ask_inst = 0

port_FlowMapping = {}

readCounterEnabled = 0

consumer = KafkaConsumer("NetManagment", bootstrap_servers='10.0.2.15:9092')

producer = KafkaProducer(bootstrap_servers='10.0.2.15:9092')

#############################################################################################
# 				INSERT IPV4 LPM ENTRIES					#
#############################################################################################
def insertipv4Entry(action_name, macAddr, ipv4_dst, egress_port, newipaddr=''):

    te = sh.TableEntry("MyIngress.ipv4_lpm")(action = action_name)
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["port"] = egress_port
    te.action["dstAddr"] = macAddr
    
    if action_name == "MyIngress.ipv4_sub_forward":
        te.action["newipaddr"] = newipaddr
        te.modify()
        return

    te.insert()

#############################################################################################
# 				DELETE IPV4 LPM ENTRIES					#
#############################################################################################
def deleteipv4Entry(action_name, macAddr, ipv4_dst, egress_port, newipaddr=''):

    te = sh.TableEntry("MyIngress.ipv4_lpm")(action = action_name)
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["port"] = egress_port
    te.action["dstAddr"] = macAddr

    if action_name == "MyIngress.ipv4_sub_forward":
        te.action["newipaddr"] = newipaddr

    te.delete()
        
#############################################################################################
# 				INSERT IPV4 SubAnswer ENTRIES					#
#############################################################################################
def insertSubAnswerEntry(ipaddr, egress_port, destMacAddr, srcAddr, ipv4_dst):
    te = sh.TableEntry("MyIngress.ipv4_sub_answer")(action = "MyIngress.ipv4_sub_answer_forward")
    te.match["hdr.ipv4.srcAddr"] = srcAddr
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["originaldestIpAddr"] = ipaddr
    te.action["port"] = egress_port
    te.action["dstMacAddr"] = destMacAddr
    te.insert()

#############################################################################################
# 				INSTANTIATE FLOW COUNTER					#
#############################################################################################
def instantiateFlowCounter(port, max_rule, min_rule):

    global readCounterEnabled
    global port_FlowMapping
    
    readCounterEnabled = 1
    
    port_FlowMapping[port] = [max_rule, min_rule, 0, 0]
    
    '''te = sh.TableEntry("MyIngress.flow_control")(action = "MyIngress.flow_check")
    te.match["hdr.ipv4.dstAddr"] = dstAddr
    te.action["maxFlows"] = max_rule
    te.action["minFlows"] = min_rule
    te.insert()'''
    
#############################################################################################
# 					Send PacketOut						#
#############################################################################################
def sendPacketOut():

    global CPU_PORT
    
    p = sh.PacketOut()
    p.payload = b'AAAA'
    p.metadata['egress_port'] = CPU_PORT
    p.send()

#############################################################################################
# 					Send PacketIn						#
#############################################################################################
def parsePacketIn(msg):
    
    value = msg.split('value: ')[2].split('"')[1]
    
    if value == None:
        return 'None'
    else:
        return value

#############################################################################################
# 					PRINT COUNTER INFO					#
#############################################################################################
def printCounter(counter):
     
    global port_FlowMapping
    
    log(" - Printing Counter " + counter + " value - ")
    
    counts = sh.CounterEntry(counter).read()
    ports_on_watch = port_FlowMapping.keys()
    
    for item in counts:
        for port in ports_on_watch:
            if item.index == int(port):
                num_packets = item.data.packet_count
                log("Number of packets on port " + port + ": " + str(num_packets))
            
#############################################################################################
# 					CHECK fLOW COUNTER					#
#############################################################################################
def checkFlowCounter(code):          

    global port_FlowMapping
    global producer
    global ask_inst
    global ask_del
    
    log(" - VERYFING CODE: " + code + " - ")
    
    if '002X' in code and ask_inst != 1:
        log(' - Asking for k8s service instantiation - ')
        msg_out = '[COMPUTATIONCONTROLLER] [INSTANTIATE] [TRIGGERED] ' + str(1)
        producer.send('ComputationManagment', msg_out.encode())
        ask_inst = 1
        ask_del = 0
        
    if 'CODEDEL' in code and ask_del != 1:
        log(' - Asking for k8s service removal - ')
        msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [TRIGGERED] ' + str(1)
        producer.send('ComputationManagment', msg_out.encode())
        ask_del = 1
        ask_inst = 0

    '''counts = sh.CounterEntry(counter).read()
    ports_on_watch = port_FlowMapping.keys()
    
    for item in counts:
        for port in ports_on_watch:
            if item.index == int(port):
                num_packets = item.data.packet_count
                
                if num_packets >= int(port_FlowMapping.get(port)[0]) and ask_inst == 0:
                    log(' - Asking for k8s service instantiation - ')
                    msg_out = '[COMPUTATIONCONTROLLER] [INSTANTIATE] [TRIGGERED] ' + port
                    producer.send('ComputationManagment', msg_out.encode())
                    ask_inst = 1
                    
                if num_packets <= int(port_FlowMapping.get(port)[1]) and ask_del == 0:
                    log(' - Asking for k8s service removal - ')
                    msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [TRIGGERED] ' + port
                    producer.send('ComputationManagment', msg_out.encode())
                    ask_del = 1
                    
                if num_packets == port_FlowMapping.get(port)[3]:
                    port_FlowMapping.get(port)[2] = port_FlowMapping.get(port)[2] + 1
                    if port_FlowMapping.get(port)[2] == 4:
                        msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [TRIGGERED] ' + port
                        producer.send('ComputationManagment', msg_out.encode())
                        ask_del = 1
                else:
                    port_FlowMapping.get(port)[3] = num_packets
                    port_FlowMapping.get(port)[2] = 0'''
    

###############################################
#		Check Action			#
###############################################
def checkAction(msg):

    global producer
    
    processor, action = msg.split(' ')[0:2]
    
    if processor != '[NETCONTROLLER]':
        return None

    if action == '[INSERT]':
        log(" - creating service route -")
        name, table, action_name, ipaddr, egress_port, newipaddr, newmacaddr = msg.split(' ')[2:]
        
        if table == 'ipv4_lpm':
            log(" - inserting entry -")
            try:
                insertipv4Entry(action_name, newmacaddr, ipaddr, egress_port, newipaddr)
            except:
                msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [RIGHTAWAY] ' + name
                producer.send('ComputationManagment', msg_out.encode())

    if action == '[DELETE]':
        log(" - deleting service route -")
        table, action_name, ipaddr, egress_port, newipaddr, newmacaddr = msg.split(' ')[2:]
        
        if table == 'ipv4_lpm':
            log(" - deleting entry -")
            deleteipv4Entry(action_name, newmacaddr, ipaddr, egress_port, newipaddr)
            
    if action == '[INSTANTIATE]':
        impl_object, port, rule_n1, rule_n2 = msg.split(' ')[2:]
        
        if impl_object == '[FLOWCOUNTER]':
            log(" - creating flow counter -")
            instantiateFlowCounter(port, rule_n1, rule_n2)

############################################################################################
def main(p4info_file_path, bmv2_file_path):

    global consumer
    global readCounterEnabled

    sleep(5)

    # Instantiate a P4Runtime helper from the p4info file
    sh.setup(
        device_id=1,
        grpc_addr='10.32.0.5:9559',
        election_id=(0, 1), # (high, low)
        config=sh.FwdPipeConfig(p4info_file_path, bmv2_file_path)
    )

    try:
    
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1e:00:1e", "10.30.0.30", "1")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1f:00:1e", "10.31.0.30", "2")
        #insertipv4Entry("MyIngress.ipv4_sub_forward", "10.30.0.30", "10.0.2.15", "4", "08:00:27:93:75:80")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:21:00:32", "10.33.0.50", "3")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1f:00:1f", "10.31.0.31", "2")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1f:00:20", "10.31.0.32", "2")
        insertSubAnswerEntry("10.30.0.30", "2", "02:42:0a:1f:00:1e", "10.0.2.15", "10.31.0.30")
        insertSubAnswerEntry("10.30.0.30", "2", "02:42:0a:1f:00:1f", "10.0.2.15", "10.31.0.31")
        insertSubAnswerEntry("10.30.0.30", "2", "02:42:0a:1f:00:20", "10.0.2.15", "10.31.0.32")
        
        packet_in = sh.PacketIn()
        
        while(True):
            if readCounterEnabled == 1:
                sendPacketOut()
                for msg in packet_in.sniff(timeout=1):
                    code = parsePacketIn(str(msg))
                    checkFlowCounter(code)
                    #printCounter("MyEgress.port_packet_counter")

            msg = consumer.poll(1000)
            
            if msg:
                for tp in msg:
                    processed_msg = msg.get(tp)[0].value.decode()
                    log(processed_msg)
                    checkAction(processed_msg)
                    processed_msg = ''
                    msg = {}

    except KeyboardInterrupt:
        print(" Shutting down.")
    except grpc.RpcError as e:
        printGrpcError(e)

    sh.teardown()
    
###############################################
#			LOG			#
###############################################
def log(msg):

    # Building the command.
    command = ['echo', msg]

    subprocess.call(command)
    
###############################################
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='P4Runtime Controller')
    parser.add_argument('--p4info', help='p4info proto in text format from p4c',
                        type=str, action="store", required=False,
                        default='/usr/src/app/p4info.txt')
    parser.add_argument('--bmv2-json', help='BMv2 JSON file from p4c',
                        type=str, action="store", required=False,
                        default='/usr/src/app/fabric.json')
    args = parser.parse_args()

    if not os.path.exists(args.p4info):
        parser.print_help()
        print("\np4info file not found: %s\nHave you run 'make'?" % args.p4info)
        parser.exit(1)
    if not os.path.exists(args.bmv2_json):
        parser.print_help()
        print("\nBMv2 JSON file not found: %s\nHave you run 'make'?" % args.bmv2_json)
        parser.exit(1)
    main(args.p4info, args.bmv2_json)

