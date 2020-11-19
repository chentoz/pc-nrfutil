import socket
import json
from nordicsemi.dfu_update import update

localIP     = "127.0.0.1"
f  = open('local.settings.json')
data = json.load(f)

localPort = data['UpdateServices']['port']
gatewayPort = data['MqttSNGateway']['port']

bufferSize  = 1024

msgFromServer   = "Hello UDP Client"
bytesToSend         = str.encode(msgFromServer)

UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
UDPServerSocket.bind((localIP, localPort))
UDPServerSocket.setblocking(True)

print("UDP server up and listening")

dev2MsgBuffer = {}
dev2TargetIPPort = {}

# Listen for incoming datagrams
while(True):
    bytesAddressPair = UDPServerSocket.recvfrom(bufferSize)
    cltMsg = bytesAddressPair[0]
    cltAddr = bytesAddressPair[1]
    clientMsg = "Message from Client:{}".format(cltMsg)
    clientIP  = "Client IP Address:{}".format(cltAddr)
    print(clientMsg)
    print(clientIP)
    update("test.zip", bytesAddressPair[1], UDPServerSocket)
    # UDPServerSocket.sendto(str.encode('Hello'), cltAddr)

f.close()

#    port = cltAddr[1]
#    cltJsonMsg = json.loads(cltMsg)
#   if port == gatewayPort:
#     target = dev2TargetIPPort.get['dev']

#     if target != None:
#         """ UDPServerSocket.sendto(cltJsonMsg['msg'], target) """

#     else:
#         dev2MsgBuffer[cltJsonMsg['dev']] = cltJsonMsg['msg']
# else:
#     dev2TargetIPPort[cltJsonMsg['dev']] = cltAddr