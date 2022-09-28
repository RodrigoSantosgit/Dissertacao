'''
	Rodrigo Santos, n mec 89180
	
	- Dissertation Project
	Network Controller - P4Switch Controller
'''
import argparse
import os
import sys
import time
from kafka import KafkaConsumer
from kafka import KafkaProducer
import subprocess
import json
import grpc
from p4.v1 import p4runtime_pb2
# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
import p4runtime_sh.shell as sh
import p4runtime_lib.helper

global port1_flux
global timestamps
global port4_flux
global CPU_PORT
global consumer
global producer
global readCounterEnabled
global port_FlowMapping
global ask_inst
global ask_del
global flows
global next

port1_flux = []
timestamps = []
port4_flux = []
next = 0
flows = []
CPU_PORT = '255'
ask_del = 1
ask_inst = 0
port_FlowMapping = {}
readCounterEnabled = 0
consumer = KafkaConsumer("NetManagment", bootstrap_servers='10.0.2.15:9092')
producer = KafkaProducer(bootstrap_servers='10.0.2.15:9092')


#############################################################################################
# 				INSERT IPV4 LPM ENTRIES					#
#############################################################################################
def insertipv4Entry(action_name, macAddr, ipv4_dst, egress_port, newipaddr='', port=''):
    te = sh.TableEntry("MyIngress.ipv4_lpm")(action = action_name)
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["port"] = egress_port
    te.action["dstAddr"] = macAddr
    
    if action_name == "MyIngress.ipv4_nat_forward":
        te.action["newipaddr"] = newipaddr
        te.action["dport"] = port
        te.modify()
        return
    te.insert()


#############################################################################################
# 				DELETE IPV4 LPM ENTRIES					#
#############################################################################################
def deleteipv4Entry(action_name, macAddr, ipv4_dst, egress_port, newipaddr='', port=''):
    te = sh.TableEntry("MyIngress.ipv4_lpm")(action = action_name)
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["port"] = egress_port
    te.action["dstAddr"] = macAddr
    if action_name == "MyIngress.ipv4_nat_forward":
        te.action["newipaddr"] = newipaddr
        te.action["dport"] = port
    te.delete()


#############################################################################################
# 				INSERT IPV4 NATAnswer ENTRIES					#
#############################################################################################
def insertNatAnswerEntry(ipaddr, egress_port, destMacAddr, srcAddr, ipv4_dst, port):
    te = sh.TableEntry("MyIngress.ipv4_nat_answer")(action = "MyIngress.ipv4_nat_answer_forward")
    te.match["standard_metadata.ingress_port"] = '4'
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["originaldestIpAddr"] = ipaddr
    te.action["port"] = egress_port
    te.action["dstMacAddr"] = destMacAddr
    te.action["sport"] = port
    te.insert()
    

#############################################################################################
# 				INSTANTIATE FLOW COUNTER					#
#############################################################################################
def instantiateFlowCounter(service, max_rule, min_rule):
    global readCounterEnabled
    global port_FlowMapping

    readCounterEnabled = 1

    port_FlowMapping[service] = [max_rule, min_rule]
    
    te = sh.TableEntry("MyIngress.flow_detection")(action = "MyIngress.update_flow")
    te.match["meta.inc_flowid"] = '11'
    te.action["min"] = min_rule
    te.action["max"] = max_rule
    te.insert()
    

#############################################################################################
# 					Send PacketOut						#
#############################################################################################
def sendPacketOut(service):

    global CPU_PORT
    global flows
    global next
    global port_FlowMapping

    p = sh.PacketOut()
    p.payload = b'monitor packet'
    p.metadata['egress_port'] = CPU_PORT
    p.metadata['min'] = port_FlowMapping[service][1]

    if len(flows) > 0:
        if next >= len(flows) - 1:
            next = 0
        else:
            next = next + 1
        
        p.metadata['flowid'] = str(flows[next])
    p.send()


#############################################################################################
# 					Send PacketIn						#
#############################################################################################
def parsePacketIn(msg):
    
    global flows
    global next
    
    value = int(msg.packet.metadata[1].value.hex(), base=16)
    flowid = int(msg.packet.metadata[2].value.hex(), base=16)
    rm_flow = int(msg.packet.metadata[3].value.hex(), base=16)
    rm_flag = int(msg.packet.metadata[4].value.hex(), base=16)
    
    if rm_flag == 1:
        flows.remove(rm_flow)
        if next > len(flows):
            next = next - 1
        #log(str(flows))
    
    if flowid not in flows:
        flows = flows + [flowid]
        #log(str(flows))
    
    if value == None or value == 0:
        return 'None'
    else:
        return value


#############################################################################################
# 					PRINT COUNTER INFO					#
#############################################################################################
def printCounter(counter):

    global port1_flux
    global timestamps 
    global port4_flux 

    counts = sh.CounterEntry(counter).read()

    for item in counts:
        if item.index == 1: 
            num_packets = item.data.packet_count
            port1_flux = port1_flux + [num_packets]
        if item.index == 4:
            num_packets = item.data.packet_count
            port4_flux = port4_flux + [num_packets]
            
    timestamps = timestamps + [time.time()]
        
    '''if timestamps[-1] - timestamps[0] > 40:
        log(str(port1_flux))
        log(str(timestamps))
        log(str(port4_flux))'''

#############################################################################################
# 					CHECK fLOW COUNTER					#
#############################################################################################
def checkFlowCounter(code):
    global port_FlowMapping
    global producer
    global ask_inst
    global ask_del
    
    if code == 600 and ask_inst != 1:
        log(' - Asking for k8s service instantiation - ')
        msg_out = '[COMPUTATIONCONTROLLER] [INSTANTIATE] [TRIGGERED] ' + list(port_FlowMapping.keys())[0]
        producer.send('ComputationManagment', msg_out.encode())
        f = open("/tmp/Teste0.txt", "a")
        f.write("kubernetes Inst Request Ts: " + str(time.time())+"\n")
        f.close()
        ask_inst = 1
        ask_del = 0
        
    if code == 900 and ask_del != 1:
        log(' - Asking for k8s service removal - ')
        msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [TRIGGERED] ' + list(port_FlowMapping.keys())[0]
        producer.send('ComputationManagment', msg_out.encode())
        f = open("/tmp/Teste0.txt", "a")
        f.write("kubernetes Del Request Ts: " + str(time.time())+"\n")
        f.close()
        ask_del = 1
        ask_inst = 0


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
        name, table, action_name, ipaddr, egress_port, newipaddr, newmacaddr, port, srcaddr = msg.split(' ')[2:]
        
        if table == 'ipv4_lpm':
            log(" - inserting entry -")
            try:
                insertipv4Entry(action_name, newmacaddr, ipaddr, egress_port, newipaddr, port)
                f = open("/tmp/Teste0.txt", "a")
                f.write("ROUTE TO KUBERNETES Ts: " + str(time.time())+"\n")
                f.close()
            except:
                msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [RIGHTAWAY] ' + name
                producer.send('ComputationManagment', msg_out.encode())
        if table == 'ipv4_nat_answer':
            log(" - inserting entry -")
            try:
                insertNatAnswerEntry(newipaddr, egress_port, newmacaddr, ipaddr, srcaddr, port)
                f = open("/tmp/Teste0.txt", "a")
                f.write("ROUTE KUBERNETES ANSWER Ts: " + str(time.time())+"\n")
                f.close()
            except:
                msg_out = '[COMPUTATIONCONTROLLER] [DELETE] [RIGHTAWAY] ' + name
                producer.send('ComputationManagment', msg_out.encode())
    if action == '[DELETE]':
        log(" - deleting service route -")
        table, action_name, ipaddr, egress_port, newipaddr, newmacaddr, port = msg.split(' ')[2:]
        
        if table == 'ipv4_lpm':
            log(" - deleting entry -")
            deleteipv4Entry(action_name, newmacaddr, ipaddr, egress_port, newipaddr, port)
            if action_name == 'MyIngress.ipv4_nat_forward':
                insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1e:00:1e", ipaddr, "1")
                f = open("/tmp/Teste0.txt", "a")
                f.write("ROUTE BACK TO SERVER Ts: " + str(time.time())+"\n")
                f.close()
            
    if action == '[INSTANTIATE]':
        impl_object, service, rule_n1, rule_n2 = msg.split(' ')[2:]
        
        if impl_object == '[FLOWCOUNTER]':
            log(" - creating flow counter -")
            instantiateFlowCounter(service, rule_n1, rule_n2)
            f = open("/tmp/Teste0.txt", "a")
            f.write("FLOW MANAGEMENT START Ts: " + str(time.time())+"\n")
            f.close()
            

############################################################################################
def main(p4info_file_path, bmv2_file_path):
    global consumer
    global readCounterEnabled
    time.sleep(5)
    # Instantiate a P4Runtime helper from the p4info file
    sh.setup(
        device_id=1,
        grpc_addr='10.32.0.5:9559',
        election_id=(0, 1), # (high, low)
        config=sh.FwdPipeConfig(p4info_file_path, bmv2_file_path)
    )
    
    f = open("/tmp/Teste0.txt", "w")
    f.write("SYSTEM TEST TIMESTAMPS\n")
    f.close()
    
    cse = sh.CloneSessionEntry(500)
    cse.add(255, 1)
    cse.insert()
    
    te = sh.TableEntry("MyIngress.ipv4_api")(action = "MyIngress.ipv4_forward")
    te.match["hdr.ipv4.srcAddr"] = "10.33.0.50"
    te.action["port"] = "1"
    te.action["dstAddr"] = "02:42:0a:1e:00:1e"
    te.insert()

    try:

        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1e:00:1e", "10.30.0.30", "1")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1f:00:1e", "10.31.0.30", "2")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:21:00:32", "10.33.0.50", "3")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1f:00:1f", "10.31.0.31", "2")
        insertipv4Entry("MyIngress.ipv4_forward", "02:42:0a:1f:00:20", "10.31.0.32", "2")
        
        packet_in = sh.PacketIn()

        while(True):
        
            #printCounter("MyIngress.flux_counter")
            
            if readCounterEnabled == 1:
            
                for key in list(port_FlowMapping.keys()):
                    sendPacketOut(key)
                    for msg in packet_in.sniff(timeout=0.020):
                        code = parsePacketIn(msg)
                        checkFlowCounter(code)

            msg = consumer.poll(20)
            
            if msg:
                for tp in msg:
                    for for_proc_msg in msg.get(tp):
                        f = open("/tmp/Teste0.txt", "a")
                        f.write("KAFKA MESSAGE Ts: " + str(time.time()) +"\n")
                        f.close()
                        processed_msg = for_proc_msg.value.decode()
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

