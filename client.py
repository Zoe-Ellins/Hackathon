#Client
import threading
from socket import *
from threading import Timer
import struct
from kblistener import KBHit

clientSocketTCP = None
stop_threads = False

def UDPclient():
    '''
    purpose : create UDP socket for cient enabling broadcast mode
    :return: UDP socket
    '''

    # create UDP socket for server
    clientSocket = socket(AF_INET, SOCK_DGRAM , IPPROTO_UDP)

    # Enable broadcasting mode
    clientSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    # Broadcast port = 13117
    clientSocket.bind(("", 13117))
    return clientSocket


def TCPclient():
    '''
    purpose : create TCP socket for client
    :return: TCP client
    '''
    print('Client started, listening for offer requests...')
    # create TCP socket for server, remote port 12000
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.setblocking(True)
    return clientSocket


def catchOffer(clientSocket):
    '''
    purpose : parsing packets received form the UDP socket - checking that they are really offer packets
    :param clientSocket: client UDP socket waiting for broadcast packets
    :return: server IP address and port for TCP connection
    '''

    try:
        msg = 0
        serverAddress = 0

        # read reply characters from socket into string
        msg, serverAddress = clientSocket.recvfrom(1024)

        # msg[:4] = Magic Cookie (4 bytes)     msg[4] = Message type (1 byte)    msg[5:7] = Server port (2 bytes)
        if msg[:4] == bytes([0xfe, 0xed, 0xbe, 0xef]) and msg[4] == 0x02:
            port = struct.unpack('>H', msg[5:7])[0]
            return serverAddress[0], int(port)
        else:
            return 0

    except Exception as e:
        return 0


def on_press ():
    '''
    purpose : clients press on keyboard
    :return: char pressed on clients keyboard
    '''
    kb=KBHit()
    global stop_threads
    while True:
        if kb.kbhit():
            #client input
            key = kb.getch()
            print(key)
            try:
                #send client input to server
                clientSocketTCP.send(str(key).encode('utf-8'))
            except Exception as e:
                break
        if stop_threads:
            break

def stop_thread():
    global stop_threads
    #stop thread that reads the clients inputs
    stop_threads = True


def main():
    global clientSocketTCP
    global stop_threads

    while True:
        clientSocketUDP = UDPclient()
        clientSocketTCP = TCPclient()
        # Catch offer
        while(True):
            serverTCPport = 0
            serverTCPip = 0

            #catch offers from broadcasts msg
            serverTCPip , serverTCPport = catchOffer(clientSocketUDP)

            if(serverTCPport is not 0):
                print (f'Received offer from {serverTCPip} attempting to connect...')
                try:
                    #trying to connect to TCP server cought from the offer
                    clientSocketTCP.connect((serverTCPip, serverTCPport))
                    break

                except Exception as e:
                    continue

        # Send server the client name
        try:
            clientSocketTCP.send(b'Shmar&Zoe\n')

            # get the start game msg from server
            startMsg = clientSocketTCP.recv(1024)
            print(startMsg.decode('utf-8'))

            # listen to clients keyboard until game ends
            listener = threading.Thread(target=on_press, daemon=True)
            listener.start()
            Timer(10, stop_thread).start()
            listener.join()
            stop_threads = False

            # get the end game msg from server
            endMsg = clientSocketTCP.recv(1024)
            print(endMsg.decode('utf-8'))

            clientSocketTCP.close()
            clientSocketUDP.close()
            print('Server disconnected, listening for offer requests...')

        except Exception as e:
            clientSocketTCP.close()
            clientSocketUDP.close()
            print('Server disconnected, listening for offer requests...')
            continue

if __name__ == "__main__":
    # execute only if run as a script
    main()