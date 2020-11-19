import socket
import json
import itertools
import functools
from struct import pack
import paho.mqtt.client as mqtt

localIP = "127.0.0.1"
f = open('local.settings.json')
local_configs = json.load(f)
f.close()

localPort = local_configs['UpdateServices']['port']
gatewayPort = local_configs['MqttSNGateway']['port']
mqtt_host = local_configs['Mosquitto']['mqtt']['host']
mqtt_port = local_configs['Mosquitto']['mqtt']['port']

bufferSize = 4096

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind(('192.168.8.169', localPort))
UDPServerSocket.setblocking(True)

print("UDP server up and listening")

dev2MsgBuffer = {}
dev2TargetIPPort = {}
g_Mac2AddrLookup = {}


def HDLC_Encode(message):
    msgLen = message.length
    encodedFrame = bytearray(msgLen * 2 + 2)
    encodedFrame[0] = 0x7e
    frameEnd = 1
    for srcIdx in range(msgLen):
        if message[srcIdx] == 0x7e:
            encodedFrame[frameEnd] = 0x7d
            frameEnd += 1
            encodedFrame[frameEnd] = 0x5e
        elif message[srcIdx] == 0x7d:
            encodedFrame[frameEnd] = 0x7d
            frameEnd += 1
            encodedFrame[frameEnd] = 0x5d
        else:
            encodedFrame[frameEnd] = message[srcIdx]
        frameEnd += 1

    encodedFrame[frameEnd] = 0x7e
    frameEnd += 1
    return encodedFrame[0, frameEnd]


def HDLC_Decode(message, rinfo, handle):
    state = 0
    frameEnd = 0
    msgLen = len(message)
    frame = bytearray(msgLen)
    totalPacket = 0
    for srcIdx in range(0, msgLen):
        if message[srcIdx] == 0x7e:
            if state == 0:
                state = 1
                continue
            elif state == 1:
                try:
                    totalPacket += 1
                    handle(frame[0, frameEnd], rinfo)
                except Exception as e:
                    print("Handling frame error :" % e)
                frame = bytearray(msgLen)
                state = 0
                frameEnd = 0
        elif message[srcIdx] == 0x7d and srcIdx + 1 < msgLen:
            if message[srcIdx + 1] == 0x5e:
                frame[frameEnd] = 0x7e
                frameEnd += 1
                srcIdx += 1
            elif message[srcIdx + 1] == 0x5d:
                frame[frameEnd] = 0x7d
                frameEnd += 1
                srcIdx += 1
            else:
                frame[frameEnd] = message[srcIdx]
                frameEnd += 1
        else:
            frame[frameEnd] = message[srcIdx]
            frameEnd += 1

    print(
        '************************************\n Total Packets: {}\n ** ********************************** \n'.
        format(totalPacket)
    )


client = mqtt.Client()


def on_connect(client, userdata, flags, rc):
    print("Connected with result code" + str(rc))
    client.subscribe('HeartBeatAck')


def on_message(client, userdata, msg):
    if msg.topic == "HeartBeatAck":
        print(
            "============================== GW HRB-ACK =============================="
        )
        print(
            "MAC : " +
            ByteArray2HexString(msg.payload[2, 2 + 6]) +
            "\n Packets : \n " +
            ByteArray2HexString(msg.payload)
        )
        rinfo = g_Mac2AddrLookup[ByteArray2HexString(msg.payload[2, 2 + 6])]
        if rinfo is None:
            return

        packet = bytearray(7) + bytearray(msg.payload)
        packet[0] = len(packet)
        packet[1] = 0x0c
        packet[2] = 0x62
        packet[3] = 'H'.encode()
        packet[4] = 'B'.encode()
        packet[5:7] = 0x0b00

        UDPServerSocket.sendto(packet, rinfo)


client.on_connect = on_connect
client.on_message = on_message
client.connect(mqtt_host, mqtt_port)
client.loop_start()


def ByteArray2HexString(byteArray, delimiter=""):
    return byteArray.hex()


def handleMqttSnMessage(message, rinfo):
    """
    docstring
    """
    data = bytearray(message)
    mqttsnMessage = data[7:]

    topic = ""
    if data[3] == 0x42:
        topic = "BLELocation"
    elif data[3] == 0x47:
        topic = "GPSLocation"
    elif data[3] == 0x4C:
        topic = "BLEGPSLocation"
    elif data[3] == 0x48:
        print(
            "HeartBeat from MAC : " +
            ByteArray2HexString(mqttsnMessage[2, 2 + 6]) +
            "\n Packets : \n " +
            ByteArray2HexString(mqttsnMessage, " ")
        )
        topic = "HeartBeat"
        g_Mac2AddrLookup[ByteArray2HexString(mqttsnMessage[2, 2 + 6])] = rinfo

    else:
        print("Unrecognized topic")
        return

    client.publish(topic=topic, payload=bytearray(mqttsnMessage))


while(True):
    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    cltMsg = bytearray(bytesAddressPair[0])
    cltAddr = bytesAddressPair[1]
    clientMsg = "Message from Client:{}".format(cltMsg)
    clientIP = "Client IP Address:{}".format(cltAddr)
    HDLC_Decode(clientMsg, rinfo=cltAddr, handle=handleMqttSnMessage)

client.loop_end()
