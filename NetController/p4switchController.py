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

import grpc

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
import p4runtime_sh.shell as sh

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2

global consumer
global producer

consumer = KafkaConsumer("NetManagment", bootstrap_servers='10.0.2.15:9092')

producer = KafkaProducer(bootstrap_servers='10.0.2.15:9092')

#############################################################################################
# 				INSERT IPV4 SUB FORWARDING ENTRIES				#
#############################################################################################
def insertipv4SubEntry(ipaddr, newipaddr, egress_port, newmacaddr):

    te = sh.TableEntry("MyIngress.ipv4_sub")(action = "MyIngress.ipv4_sub_forward")
    te.match["hdr.ipv4.dstAddr"] = ipaddr
    te.action["newipaddr"] = newipaddr
    te.action["port"] = egress_port
    te.action["dstAddr"] = newmacaddr
    te.insert()

#############################################################################################
# 				DELETE IPV4 SUB FORWARDING ENTRIES				#
#############################################################################################
def deleteipv4SubEntry(ipaddr, newipaddr, egress_port, newmacaddr):
    
    te = sh.TableEntry("MyIngress.ipv4_sub")(action = "MyIngress.ipv4_sub_forward")
    te.match["hdr.ipv4.dstAddr"] = ipaddr
    te.action["newipaddr"] = newipaddr
    te.action["port"] = egress_port
    te.action["dstAddr"] = newmacaddr
    te.delete()

#############################################################################################
# 				INSERT IPV4 FORWARDING ENTRIES				#
#############################################################################################
def insertipv4Entry(macAddr, ipv4_dst, egress_port):

    te = sh.TableEntry("MyIngress.ipv4_lpm")(action = "MyIngress.ipv4_forward")
    te.match["hdr.ipv4.dstAddr"] = ipv4_dst
    te.action["port"] = egress_port
    te.action["dstAddr"] = macAddr
    te.insert()

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
        table, ipaddr, egress_port, newipaddr, newmacaddr = msg.split(' ')[2:]
        
        if table == 'IPV4SubEntry':
            log(" - inserting entry -")
            insertipv4SubEntry(ipaddr, newipaddr, egress_port, newmacaddr)

    if action == '[DELETE]':
        log(" - deleting service route -")
        table, ipaddr, egress_port, newipaddr, newmacaddr = msg.split(' ')[2:]
        
        if table == 'IPV4SubEntry':
            log(" - deleting entry -")
            res = deleteipv4SubEntry(ipaddr, newipaddr, egress_port, newmacaddr)

############################################################################################

def main(p4info_file_path, bmv2_file_path):

    global consumer

    sleep(5)

    # Instantiate a P4Runtime helper from the p4info file
    sh.setup(
        device_id=1,
        grpc_addr='10.32.0.5:9559',
        election_id=(0, 1), # (high, low)
        config=sh.FwdPipeConfig(p4info_file_path, bmv2_file_path)
    )

    try:
    
        insertipv4Entry("02:42:0a:1e:00:1e", "10.30.0.30", "1")
        insertipv4Entry("02:42:0a:1f:00:1e", "10.31.0.30", "2")
        
        while(True):
            for msg in consumer:
                processed_msg = msg.value.decode()
                log(processed_msg)
                checkAction(processed_msg)
                processed_msg = ''

        ''' # Write the rules that tunnel traffic from h1 to h2
        writeTunnelRules(p4info_helper, ingress_sw=s1, egress_sw=s2, tunnel_id=100,
                         dst_eth_addr="08:00:00:00:02:22", dst_ip_addr="10.0.2.2")

        # Write the rules that tunnel traffic from h2 to h1
        writeTunnelRules(p4info_helper, ingress_sw=s2, egress_sw=s1, tunnel_id=200,
                         dst_eth_addr="08:00:00:00:01:11", dst_ip_addr="10.0.1.1")

        # TODO Uncomment the following two lines to read table entries from s1 and s2
        readTableRules(p4info_helper, s1)
        readTableRules(p4info_helper, s2)

        # Print the tunnel counters every 2 seconds
        while True:
            sleep(2)
            print('\n----- Reading tunnel counters -----')
            printCounter(p4info_helper, s1, "MyIngress.ingressTunnelCounter", 100)
            printCounter(p4info_helper, s2, "MyIngress.egressTunnelCounter", 100)
            printCounter(p4info_helper, s2, "MyIngress.ingressTunnelCounter", 200)
            printCounter(p4info_helper, s1, "MyIngress.egressTunnelCounter", 200) '''

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
                        default='/usr/src/app/chassis.pb.txt')
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

