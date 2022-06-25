#!/usr/bin/env python3
import argparse
import os
import sys
from time import sleep

import grpc

# Import P4Runtime lib from parent utils dir
# Probably there's a better way of doing this.
import p4runtime_sh.shell as sh

SWITCH_TO_HOST_PORT = 1
SWITCH_TO_SWITCH_PORT = 2
    
#############################################################################################
# 				INSERT ROUTING V4 ENTRIES					#
#############################################################################################
def insertRoutingv4Entry(ipv4_dst, next_id):

    te = sh.TableEntry("FabricIngress.forwarding.routing_v4")(action = "FabricIngress.forwarding.set_next_id_routing_v4")
    te.match["ipv4_dst"] = ipv4_dst
    te.action["next_id"] = next_id
    te.insert()

############################################################################################

def main(p4info_file_path, bmv2_file_path):
    # Instantiate a P4Runtime helper from the p4info file
    sh.setup(
        device_id=1,
        grpc_addr='10.2.0.5:9559',
        election_id=(0, 1), # (high, low)
        config=sh.FwdPipeConfig(p4info_file_path, bmv2_file_path)
    )
     
    try:   
        # Insert basic entries needed for ipv4 routing
        insertRoutingv4Entry("10.4.0.4", "1")
        print("Inserted entry 10.4.0.4 --> 1\n")

        insertRoutingv4Entry("10.3.0.3", "2")
        print("Inserted entry 10.3.0.3 --> 2\n")

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
