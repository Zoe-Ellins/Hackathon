# Server
from socket import *
import time
import threading
import selectors
import binascii

under10sec = True
clientSocketList = []
group1 = []
group2 = []
counter_group1 = 0
counter_group2 = 0
counter = 0


def UDPserver():
    serverHost = '10.100.102.33'
    serverPort = 5555
    serverSocket = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)  # create UDP socket
    #serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)  # TODO -check if needed
    # Enable broadcasting mode
    serverSocket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

    #serverSocket.bind((serverHost, 13117))
    print(f'Server started, listening on IP address {serverHost}')
    return serverSocket


def TCPserver():
    serverHost = '10.100.102.33'
    serverPort = 5555
    serverSocket = socket(AF_INET, SOCK_STREAM)  # create TCP welcoming socket
    serverSocket.bind((serverHost, serverPort))
    serverSocket.listen(1)  # server begins listening for incoming TCP requests
    serverSocket.setblocking(True)
    return serverSocket


def sendBroadcastOverUDP(start, serverSocket):
    global under10sec
    time.clock()  # start counting 10 sec
    elapsed = 0
    while elapsed < 10:
        elapsed = time.time() - start
        print('sending offers')  # TODO - remove
        msg = hex(0xfeedbeef0215B3)  # 0xfeedbeef = magic cookie , 0x02 = offer msg , 0x007C = TCP server port (5555)
        serverSocket.sendto(binascii.unhexlify(msg[2:]), ('10.100.102.255', 13117))
        time.sleep(1)

    under10sec = False


def connectClient(selector, serverSocketTCP):
    global group1
    global group2
    global clientSocketList
    global counter

    serverSocketTCP.settimeout(10)
    print('in while loop = connectAllClients')
    connectionSocket, addr = serverSocketTCP.accept()  # server waits on accept() for incoming requests, new socket created on return
    connectionSocket.setblocking(True)

    print('after accept')#TODO - remove

    # get client name
    try:
        clientName = connectionSocket.recv(1024).decode('utf-8')  # read bytes from socket
        print(clientName) #TODO - remove

        connectionSocket.setblocking(False)

        if counter % 2 == 0:
            print(f'client {clientName} is added to group1')#TODO - remove
            group1.append(clientName)
            counter += 1
            selector.register(connectionSocket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=1)
        else:
            print(f'client {clientName} is added to group2')#TODO - remove
            group2.append(clientName)
            counter += 1
            selector.register(connectionSocket, selectors.EVENT_READ | selectors.EVENT_WRITE, data=2)

        clientSocketList.append(connectionSocket)

    except Exception as e:
        return


def game(conn, groupNumber):
    global counter_group1
    global counter_group2

    try:
        msg = conn.recv(1024)
        print(f'group number = {groupNumber} , msg is = {msg}')
        if groupNumber == 1:
            counter_group1 += 1
        if groupNumber == 2:
            print(f'group2counter = {counter_group2}')
            counter_group2 += 1


    except Exception as e:
        return



def sendStartGameMsg(conn):
    print('in function --- sendStartGameMsg')#TODO-remove
    global group1
    global group2

    group1Name = ""
    for name in group1:
        group1Name+=name

    group2Name = ""
    for name in group2:
        group2Name += name

    msg = f'Welcome to Keyboard Spamming Battle Royale.\n' \
          f'Group 1\n:' \
          f'==\n' \
          f'{group1Name}\n' \
          f'Group 2:\n' \
          f'==\n' \
          f'{group2Name}\n' \
          f'Start pressing keys on your keyboard as fast as you can!!'

    try:
        conn.send(msg.encode('utf-8'))
    except Exception as e:
        return

def displayWinner(conn):
    global counter_group2
    global counter_group1
    global group1
    global group2

    group1Name = ""
    for name in group1:
        group1Name += name

    group2Name = ""
    for name in group2:
        group2Name += name

    msg = f'Its a tie ! \n' \
          f'Group 1 and Group 2 typed in {counter_group1} characters\n' \
          f'Congratulations to you all !'

    if counter_group1 > counter_group2:
        msg = f'Game over!\n' \
              f'Group 1 typed in {counter_group1} characters\n' \
              f'Group 2 typed in {counter_group2} characters\n' \
              f'Group 1 wins!\n' \
              f'Congratulations to the winners:\n' \
              f'==\n' \
              f'{group1Name}'

    elif counter_group2 > counter_group1:
        msg = f'Game over!\n' \
              f'Group 1 typed in {counter_group1} characters\n' \
              f'Group 2 typed in {counter_group2} characters\n' \
              f'Group 2 wins!\n' \
              f'Congratulations to the winners:\n' \
              f'==\n' \
              f'{group2Name}'

    print(msg)  # TODO - do we need to print in the servers side and send the msg to all clients ?
    try:
        conn.send(msg.encode('utf-8'))
    except Exception as e:
        return

def main():
    global group1
    global group2
    global counter_group1
    global counter_group2
    global under10sec
    global clientSocketList

    # connect TCP and UDP sockets
    serverSocketUDP = UDPserver()
    serverSocketTCP = TCPserver()

    sel = selectors.DefaultSelector()
    sel.register(serverSocketTCP, selectors.EVENT_READ, data=None)

    while 1:
        # Send offers by broadcast and register all clients to selector
        start = time.time()
        thread = threading.Thread(target=sendBroadcastOverUDP, args=(start, serverSocketUDP),
                                  daemon=True)  # create thread for UDP
        thread.start()

        while under10sec:
            events = sel.select(timeout=10)
            for key, mask in events:
                if mask & selectors.EVENT_READ and key.data==None:
                    connectClient(sel, serverSocketTCP)

        # Send the message to start the game
        if len(group1)!=0 or len(group1)!=0:
            events = sel.select()
            for key, mask in events:
                if mask & selectors.EVENT_WRITE:
                    sendStartGameMsg(key.fileobj)

            # Play game for 10 sec
            start = time.time()
            elapsed = 0
            while elapsed < 10:
                elapsed = time.time() - start

                events = sel.select()
                for key, mask in events:
                    if mask & selectors.EVENT_READ:
                        game(key.fileobj, key.data)

            # Display winners
            events = sel.select()
            for key, mask in events:
                if mask & selectors.EVENT_WRITE:
                    displayWinner(key.fileobj)

            print('Game over, sending out offer requests...')
            # Close all connections to TCP server socket
            for conn in clientSocketList:
                sel.unregister(conn)
                conn.close()

        # Reset groups lists
        group1 = []
        group2 = []
        clientSocketList = []

        # Reset group counters
        counter_group1 = 0
        counter_group2 = 0
        under10sec = True
        counter = 0




if __name__ == "__main__":
    # execute only if run as a script
    main()