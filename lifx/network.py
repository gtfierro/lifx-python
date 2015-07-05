

import socket
import struct
import binascii
from time import time

from . import packetcodec

IP = '0.0.0.0'
BCAST = '255.255.255.255'
PORT = 56700

targetaddr = []
connection = None
debug = True
site = b'\00\00\00\00\00\00'

SCAN_TIMEOUT = 2

def connect(timeout = SCAN_TIMEOUT):
    global connection, targetaddr, site
    
    if debug:
        print("Attempting to connect...")
    
    #Set up the UDP socket for communications.
    udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    udpSock.bind((IP, PORT))
    
    #Generate and send the GetPANGateway packet to find bulbs. Send it 5 times for luck.
    p = packetcodec.Packet(packetcodec.GetPANGatewayPayload())
    
    for i in range(5):
        udpSock.sendto(p.__bytes__(), (BCAST, PORT))
    
    #We check that we get at least one PAN gateway back - with the new firmware there will be several
    udpSock.settimeout(0.1)
    
    startTime = time()
    
    packets = []
    
    if debug:
        print("Starting network scan...")
    
    while time() - startTime < timeout:
        try:
            data, addr = udpSock.recvfrom(1024)
            packet = packetcodec.decode_packet(data)
            packet.ipAddress = addr[0]
            if packet is not None and isinstance(packet.payload, packetcodec.PANGatewayPayload):
                packets.append(packet)
                targetaddr.append(addr)
                if debug:
                    print("Found a light at %r" % packet.ipAddress)
        except socket.timeout:
            pass
        
    if debug:
        for p in packets:
            print("Found a light at %r" % p.ipAddress)
        
    udpSock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
    
    connection = udpSock
    
    site = packet.site
    
    if debug:
        print('Established a connection with %r' % binascii.hexlify(site))

def sendpacket(p):
    global connection, targetaddr, site
    
    if connection is None:
        connect()
        
    connection.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 0)
    
    p.site = site
        
    for thisGateway in targetaddr:
        if debug:
            print("Send packet:  %r" % binascii.hexlify(p.__bytes__()))
            print("IP:           %r" % thisGateway[0])
            print("Port:         %r" % thisGateway[1])
        connection.sendto(p.__bytes__(), thisGateway)

def recvpacket(timeout = None):
    global connection
    if connection is None:
        connect()
    #connection.settimeout(timeout)
    #try:
    #    lengthdatum, addr = connection.recvfrom(2)
    #except socket.timeout:
    #    return None
    #connection.settimeout(None)
    #try:
    #    (length, ) = struct.unpack('<H', lengthdatum)
    #except struct.error:
    #    connect()
    #    return None
    #data, addr = connection.recvfrom(length - 2)
    try:
        data, addr = connection.recvfrom(1024)
    except socket.timeout:
        return None
    packet = packetcodec.decode_packet(data)
    if debug:
        print('recvpacket(): ', packet)
    return packet

def listenforpackets(seconds, desired = None, target = None):
    start = time()
    packets = []
    if debug:
        print('listenforpackets() Start: ', start)
    while time() - start < seconds:
        p = recvpacket(0.1)
        if p is not None:
            packets.append(p)
            if desired is not None and isinstance(p.payload, desired):
                if target is not None and p.target != target:
                    continue
                return packets
    return packets

