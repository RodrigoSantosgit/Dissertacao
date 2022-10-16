/* -*- P4_16 -*- */
#include <core.p4>
#include <v1model.p4>

const bit<16> TYPE_IPV4 = 0x800;
const bit<8> UDP = 0x11;
const bit<8> TCP = 0x06;
const bit<32> NUM_PORTS = 512;
const bit<9> CPU_PORT = 255;
const bit<32> CPU_CLONE_SESSION_ID = 500;

/*************************************************************************
*********************** H E A D E R S  ***********************************
*************************************************************************/
typedef bit<9>  egressSpec_t;
typedef bit<48> macAddr_t;
typedef bit<32> ip4Addr_t;
typedef bit<32> PacketCounter_t;

#define REGISTER_LENGTH 64
#define REGISTER_CELL_BIT_WIDTH 16
#define PKT_INSTANCE_TYPE_NORMAL 0

@controller_header("packet_out")
header packet_out_header_t {
    bit<16> egress_port;
}
@controller_header("packet_in")
header packet_in_header_t {
    bit<16> ingress_port;
    bit<16> code;
}
header ethernet_t {
    macAddr_t dstAddr;
    macAddr_t srcAddr;
    bit<16>   etherType;
}
header ipv4_t {
    bit<4>    version;
    bit<4>    ihl;
    bit<8>    diffserv;
    bit<16>   totalLen;
    bit<16>   identification;
    bit<3>    flags;
    bit<13>   fragOffset;
    bit<8>    ttl;
    bit<8>    protocol;
    bit<16>   hdrChecksum;
    ip4Addr_t srcAddr;
    ip4Addr_t dstAddr;
}
header udp_t {
    bit<16> sport;
    bit<16> dport;
    bit<16> len;
    bit<16> checksum;
}
header tcp_t {
    bit<16> srcPort;
    bit<16> dstPort;
    bit<32> seqNo;
    bit<32> ackNo;
    bit<4>  dataOffset;
    bit<3>  res;
    bit<3>  ecn;
    bit<6>  ctrl;
    bit<16> window;
    bit<16> checksum;
    bit<16> urgentPtr;
}
struct metadata {
    /* empty */
    bit<16> service_id;
    bit<16> inc_flowid;
    bit<32> flows_index1;
    bit<32> flows_index2;
    bit<32> flows_index3;
    bit<16> value1;
    bit<16> value2;
    bit<16> value3;
    bit<16> flow_count;
    bit<16> udp_length;
    bit<16> max;
    bit<8> counted;
    
    @field_list(0)
    bit<16> code;
    
}
struct headers {
    ethernet_t   ethernet;
    ipv4_t       ipv4;
    udp_t        udp;
    tcp_t        tcp;
    packet_out_header_t packet_out;
    packet_in_header_t packet_in;
}
/*************************************************************************
*********************** P A R S E R  ***********************************
*************************************************************************/
parser MyParser(packet_in packet,
                out headers hdr,
                inout metadata meta,
                inout standard_metadata_t standard_metadata) {
    state start {
        transition select(standard_metadata.ingress_port) {
            CPU_PORT: parse_packet_out;
            default: parse_ethernet;
        }
    }
    state parse_packet_out {
        packet.extract(hdr.packet_out);
        transition parse_ethernet;
    }
    state parse_ethernet {
        packet.extract(hdr.ethernet);
        transition select(hdr.ethernet.etherType) {
            TYPE_IPV4: parse_ipv4;
            default: accept;
        }
    }
    state parse_ipv4 {
        packet.extract(hdr.ipv4);
        transition select(hdr.ipv4.protocol){
            UDP: parse_udp;
            TCP: parse_tcp;
            default: accept;
        }
    }
    
    state parse_tcp {
        packet.extract(hdr.tcp);
        transition accept;
    }
    state parse_udp {
        packet.extract(hdr.udp);
        meta.udp_length = hdr.ipv4.totalLen - 20;
        transition accept;
    }
}
/*************************************************************************
************   C H E C K S U M    V E R I F I C A T I O N   *************
*************************************************************************/
control MyVerifyChecksum(inout headers hdr, inout metadata meta) {
    apply {  }
}
/*************************************************************************
**************  I N G R E S S   P R O C E S S I N G   *******************
*************************************************************************/
control MyIngress(inout headers hdr,
                  inout metadata meta,
                  inout standard_metadata_t standard_metadata) {
    
    register<bit<REGISTER_CELL_BIT_WIDTH>>(REGISTER_LENGTH) flows_register1;
    register<bit<REGISTER_CELL_BIT_WIDTH>>(1) count_register;

    action drop() {
        mark_to_drop(standard_metadata);
    }
    
    action l2_forward(macAddr_t dstAddr, egressSpec_t port){
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        standard_metadata.egress_spec = port;
    }
    
    action update_flow(bit<16>max) {
    
        hash(meta.flows_index1, HashAlgorithm.crc16, (bit<16>)0, {hdr.udp.dport, hdr.ipv4.dstAddr, hdr.ipv4.protocol, hdr.udp.sport, hdr.ipv4.srcAddr}, (bit<16>) REGISTER_LENGTH);
        hash(meta.flows_index2, HashAlgorithm.csum16, (bit<16>)0, {hdr.udp.dport, hdr.ipv4.dstAddr, hdr.ipv4.protocol, hdr.udp.sport, hdr.ipv4.srcAddr}, (bit<16>) REGISTER_LENGTH);
        hash(meta.flows_index3, HashAlgorithm.xor16, (bit<16>)0, {hdr.udp.dport, hdr.ipv4.dstAddr, hdr.ipv4.protocol, hdr.udp.sport, hdr.ipv4.srcAddr}, (bit<16>) REGISTER_LENGTH);
        
        flows_register1.read(meta.value1, (bit<32>)meta.flows_index1);
        flows_register1.read(meta.value2, (bit<32>)meta.flows_index2);
        flows_register1.read(meta.value3, (bit<32>)meta.flows_index3);
        
        meta.value1 = meta.value1 + 1;
        meta.value2 = meta.value2 + 1;
        meta.value3 = meta.value3 + 1;
        
        flows_register1.write(meta.flows_index1, meta.value1);
        flows_register1.write(meta.flows_index2, meta.value2);
        flows_register1.write(meta.flows_index3, meta.value3);

        meta.max = max;
        meta.counted = (bit<8>)0;
        
    }
    
    action clone_packet(){
        // Clone from ingress to egress pipeline
        clone_preserving_field_list(CloneType.I2E, CPU_CLONE_SESSION_ID, 0);
    }
    
    action ipv4_forward_api(macAddr_t dstAddr, egressSpec_t port) { 
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.ethernet.srcAddr = hdr.ethernet.dstAddr;
        hdr.ethernet.dstAddr = dstAddr;
        standard_metadata.egress_spec = port;
    }
    
    action ipv4_forward() { 
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
    }
    
    action ipv4_nat_forward(ip4Addr_t dstipaddr, bit<16> dport) {
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.ipv4.dstAddr = dstipaddr;
        hdr.udp.dport = dport;
    }

    action ipv4_nat_answer_forward(ip4Addr_t originaldestIpAddr, bit<16> sport) {
        hdr.ipv4.ttl = hdr.ipv4.ttl - 1;
        hdr.ipv4.srcAddr = originaldestIpAddr;
        hdr.udp.sport = sport;
    }

    table ipv4_nat_answer {
        key = {
            standard_metadata.ingress_port: exact;
            hdr.ipv4.srcAddr: lpm;
        }
        actions = {
            ipv4_nat_answer_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }

    table ipv4_lpm {
        key = {
            hdr.ipv4.dstAddr: lpm;
        }
        actions = {
            ipv4_forward;
            ipv4_nat_forward;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }
    
    table ipv4_api {
        key = {
            hdr.ipv4.srcAddr: lpm;
        }
        actions = {
            ipv4_forward_api;
            drop;
            NoAction;
        }
        size = 1024;
        default_action = drop();
    }
    
    table flow_detection {
        key = {
            hdr.udp.dport: exact;
            hdr.ipv4.dstAddr: exact;
            hdr.ipv4.protocol: exact;
        }
        actions = {
            update_flow;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }
    
    table l2_forwarding{
        key = {
            hdr.ipv4.dstAddr: exact;
        }
        actions = {
            l2_forward;
            NoAction;
        }
        size = 1024;
        default_action = NoAction();
    }
    
    apply {
        if (standard_metadata.ingress_port == CPU_PORT) {
            // Packet received from CPU_PORT, this is a packet-out sent by the
            // controller. Skip table processing, set the egress port as
            // requested by the controller (packet_out header) and remove the
            // packet_out header.
            standard_metadata.egress_spec = (bit<9>)hdr.packet_out.egress_port;
            hdr.packet_out.setInvalid();
            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = (bit<16>)standard_metadata.ingress_port;
            hdr.packet_in.code = 16w0;
            
        } 
        else if (hdr.ipv4.isValid()) {
            
            if (flow_detection.apply().hit){
                if (meta.value1 == (bit<16>)1){
                    if (meta.counted != (bit<8>)1){
                        count_register.read(meta.flow_count, (bit<32>)0);
                        meta.flow_count = meta.flow_count + 1;
                        count_register.write((bit<32>)0, meta.flow_count);
                        meta.counted = (bit<8>)1;
                        if (meta.flow_count >= meta.max){
                            meta.code = (bit<16>) 600;
                            clone_packet();
                        }
                    }
                }
                else if (meta.value2 == (bit<16>)1){
                    if (meta.counted != (bit<8>)1){
                        count_register.read(meta.flow_count, (bit<32>)0);
                        meta.flow_count = meta.flow_count + 1;
                        count_register.write((bit<32>)0, meta.flow_count);
                        meta.counted = (bit<8>)1;
                        if (meta.flow_count >= meta.max){
                            meta.code = (bit<16>) 600;
                            clone_packet();
                        }
                    }
                }
                else if (meta.value3 == (bit<16>)1){
                    if (meta.counted != (bit<8>)1){
                        count_register.read(meta.flow_count, (bit<32>)0);
                        meta.flow_count = meta.flow_count + 1;
                        count_register.write((bit<32>)0, meta.flow_count);
                        meta.counted = (bit<8>)1;
                        if (meta.flow_count >= meta.max){
                            meta.code = (bit<16>) 600;
                            clone_packet();
                        }
                    }
                }
                
            }
            
            if (ipv4_api.apply().miss){
                if (ipv4_nat_answer.apply().miss){
                    ipv4_lpm.apply();
                }
                l2_forwarding.apply();
            }
        }
    }
}
/*************************************************************************
****************  E G R E S S   P R O C E S S I N G   *******************
*************************************************************************/
control MyEgress(inout headers hdr,
                 inout metadata meta,
                 inout standard_metadata_t standard_metadata) {
        
    apply {
       
       if (standard_metadata.instance_type != PKT_INSTANCE_TYPE_NORMAL) {
            // Process cloned packet
            hdr.packet_in.setValid();
            hdr.packet_in.ingress_port = (bit<16>)standard_metadata.ingress_port;
            hdr.packet_in.code = meta.code;
        }
    }
}
/*************************************************************************
*************   C H E C K S U M    C O M P U T A T I O N   **************
*************************************************************************/
control MyComputeChecksum(inout headers  hdr, inout metadata meta) {
     apply {
        update_checksum(
        hdr.ipv4.isValid(),
            { hdr.ipv4.version,
              hdr.ipv4.ihl,
              hdr.ipv4.diffserv,
              hdr.ipv4.totalLen,
              hdr.ipv4.identification,
              hdr.ipv4.flags,
              hdr.ipv4.fragOffset,
              hdr.ipv4.ttl,
              hdr.ipv4.protocol,
              hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr },
            hdr.ipv4.hdrChecksum,
            HashAlgorithm.csum16);
         
        update_checksum_with_payload(
        hdr.ipv4.dstAddr == 0x0a00020f || hdr.ipv4.srcAddr == 0x0a1e001e,
            { hdr.ipv4.srcAddr,
              hdr.ipv4.dstAddr,
              8w0,
              hdr.ipv4.protocol,
              meta.udp_length,
              hdr.udp.sport, 
              hdr.udp.dport, 
              hdr.udp.len },
            hdr.udp.checksum,
            HashAlgorithm.csum16);
     }
}
/*************************************************************************
***********************  D E P A R S E R  *******************************
*************************************************************************/
control MyDeparser(packet_out packet, in headers hdr) {
    apply {
        packet.emit(hdr.packet_in);
        packet.emit(hdr.ethernet);
        packet.emit(hdr.ipv4);
        packet.emit(hdr.udp);
        packet.emit(hdr.tcp);
    }
}
/*************************************************************************
***********************  S W I T C H  *******************************
*************************************************************************/
V1Switch(
MyParser(),
MyVerifyChecksum(),
MyIngress(),
MyEgress(),
MyComputeChecksum(),
MyDeparser()
) main;
