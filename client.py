#Client
import threading
from socket import *
from threading import Timer
import struct
from kblistener import KBHit

clientSocketTCP = None
stop_threads = False

def UDPclient():
    clientSocket = socket(AF_INET, SOCK_DGRAM , IPPROTO_UDP) # create UDP socket for server

    # clientSocket.setsockopt(SOL_SOCKET, SO_REUSEPORT, 1)

    # Enable broadcasting mode
    clientSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    clientSocket.bind(("", 13117))
    return clientSocket


def TCPclient():
    print ('Client started, listening for offer requests...')
    clientSocket = socket(AF_INET, SOCK_STREAM) # create TCP socket for server, remote port 12000
    clientSocket.setblocking(True) #TODO - do we need to change it to false later?
    return clientSocket


def catchOffer(clientSocket):
    try:
        msg = 0
        serverAddress = 0
        print('looking for offers') #TODO - remove
        msg, serverAddress = clientSocket.recvfrom(1024)  # read reply characters from socket into string

        if msg[:4] == bytes([0xfe, 0xed, 0xbe, 0xef]) and msg[4] == 0x02:
            port = struct.unpack('>H', msg[5:7])[0]
            return serverAddress[0], int(port)
        else:
            return 0

    except Exception as e:
        return 0


def on_press ():
    kb=KBHit()
    global stop_threads
    while True:
        if kb.kbhit():
            key = kb.getch()
            print(key)
            try:
                clientSocketTCP.send(str(key).encode('utf-8'))
            except Exception as e:
                break
        if stop_threads:
            break

def stop_thread():
    global stop_threads
    stop_threads = True


def main():
    global clientSocketTCP
    global stop_threads

    clientSocketUDP = UDPclient() #TODO - do we need to rellocate this socket to the while?

    while True:
        clientSocketTCP = TCPclient()
        # Catch offer
        while(True):
            serverTCPport = 0
            serverTCPip = 0
            serverTCPip , serverTCPport = catchOffer(clientSocketUDP)
            if(serverTCPport is not 0):
                print (f'Received offer from {serverTCPip} attempting to connect...')  #TODO - check why i keep receiving offers even though the server is closed ?
                try:
                    print(f'trying to connect to server with ip {serverTCPip} and port number {serverTCPport} ')
                    clientSocketTCP.connect((serverTCPip, serverTCPport))
                    print('after trying to connect to server')
                    break
                except Exception as e:
                    print(e)
                    continue
        print('trying to send the client name') #TODO - remove
        # Send server the client name
        try:
            clientSocketTCP.send(b'zoe\n')
            print('after sending the client name')  # TODO - remove

            # get the start game msg from server
            startMsg = clientSocketTCP.recv(1024)
            print(startMsg.decode('utf-8'))

            # Collect events until released
            listener = threading.Thread(target=on_press, daemon=True)
            listener.start()
            Timer(10, stop_thread).start()
            listener.join()
            stop_threads = False

            # get the end game msg from server
            endMsg = clientSocketTCP.recv(1024)
            print(endMsg.decode('utf-8'))

            clientSocketTCP.close()
            print('Server disconnected, listening for offer requests...')

        except Exception as e:
            clientSocketTCP.close()
            print('Server disconnected, listening for offer requests...')
            continue

if __name__ == "__main__":
    # execute only if run as a script
    main()