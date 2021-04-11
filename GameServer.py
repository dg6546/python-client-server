#3035239404
#Lee Ming Tsun
#8/Mar/2020

import socket
import threading
import sys
import random
import select
import os

users = {} # save users' information from txt
idCount = 0 # how many users connected
games = {} # dictionary to save rooms
gamesCount = 10 # max no. of games
lock = threading.Lock() # thread lock

def thd_func(client, clientID, lock):
    connectionSocket, addr = client
    connectionSocket.setblocking(1)
    loggedIn = False
    ip = 0
    port = 0
    while not loggedIn:
        try:
            sentence = connectionSocket.recv(1024)
        except socket.error as err:
            print("Recv error: ", err)
            break
        msg = ''
        decodedSentence = sentence.decode()
        ip = addr[0]
        port = addr[1]
        print(f"{ip}:{port} : {decodedSentence}")
        rmsg = str(decodedSentence).split(' ')
        command = rmsg[0]
        if command == "/login":
            user_name = rmsg[1]
            password = rmsg[2]
            if user_name in users and users[user_name] == password:
                #login success
                msg = "1001 Authentication successful"
                connectionSocket.send(msg.encode())
                loggedIn = True
            else:
                #login failed
                msg = "1002 Authentication failed"
                connectionSocket.send(msg.encode())
    #logged in
    userID = clientID
    userExit = False
    playingGame = False
    game = None
    while not userExit and loggedIn:
        try:
            sentence = connectionSocket.recv(1024) #get input from clients
        except socket.error as e:
            break
        except:
            raise
        decodedSentence = sentence.decode()
        print(f"{ip}:{port} : {decodedSentence}")
        rmsg = str(decodedSentence).split(' ')    
        command = rmsg[0]
        if command == "/exit": #exit
            if not playingGame:
                msg = "4001 Bye bye"
                connectionSocket.send(msg.encode())
                userExit = True
            else:
                msg = "Please finish the game first"
                connectionSocket.send(msg.encode())
        elif command == "/list": #list rooms
            msg = "3001 " + str(gamesCount) + " "
            for i in range(gamesCount):
                msg += str(games[i].count) + " "
            connectionSocket.send(msg.encode())
        elif command == "/enter": # join
            if not playingGame:
                try:
                    gameID = rmsg[1]
                except IndexError:
                    msg = "not a valid room"
                    connectionSocket.send(msg.encode())
                    break
                gameID = int(rmsg[1])-1 # if user inputs 1 then the index of room will be 0
                if gameID in games:
                    game = games[gameID]
                    lock.acquire() # lock acquired
                    valid = game.join(userID)
                    lock.release() # lock released
                    if valid:
                        ready = game.getReady()
                        if not ready: #if game is not ready, traps him into wait
                            msg = "3011 Wait"
                            connectionSocket.send(msg.encode())
                            while not ready:
                                ready = game.getReady()
                        #Game started
                        msg = "3012 Game started. Please guess true or false"
                        connectionSocket.send(msg.encode())
                        playingGame = True # The player is in a game
    
                    else: # user input is not a valid room
                        msg = "not a valid room"
                        connectionSocket.send(msg.encode())

                else:
                    #no such room
                    msg = "no such room"
                    connectionSocket.send(msg.encode())
            else: # he is already in a game
                msg = "you are already in a game"
                connectionSocket.send(msg.encode()) 
        elif command == "/guess":
            if playingGame: # he joined a game
                try:
                    playedByUser = rmsg[1]
                except IndexError:
                    msg = "not a valid room"
                    connectionSocket.send(msg.encode())
                    break
                lock.acquire()
                game.play(userID, playedByUser) # put the play in the game
                lock.release()
                while not game.bothWent(): # wait until both players played
                    pass
                winner = game.winner()
                if winner == userID: #he wins
                    msg = "3021 You are the winner"
                    connectionSocket.send(msg.encode())
                elif winner == -1: #tie
                    msg = "3023 The result is a tie"
                    connectionSocket.send(msg.encode())
                else: #he lost
                    msg = "3022 You lost this game"
                    connectionSocket.send(msg.encode())
                lock.acquire()
                game.received(userID)
                if game.bothReceived():
                    game.reset()
                lock.release()
                playingGame = False
            else: # player is not in a game
                msg = "You are not in a game"
                connectionSocket.send(msg.encode())
        else:
            msg = "4002 Unrecognized message"
            connectionSocket.send(msg.encode())
    try: #try to close client socket
        connectionSocket.shutdown(2)
        connectionSocket.close()
    except socket.error as e:
        print(e)
    if game: #if player is still in a game, kick him out
        game.leave(userID)
    if userExit:
        print(f'{ip}:{port} Client disconnected peacefully')
    elif not loggedIn:
        print(f'{ip}:{port} Client disconnected by exception')
    else:
        print(f'{ip}:{port} Client disconnected by exception')


serverSocket = socket.socket()
def main(argv):
    # read username and password from txt
    filePath = os.path.abspath(argv[2]) + "\\UserInfo.txt"
    try:
        fsize = os.path.getsize(filePath)
    except os.error as emsg:
        print("File error: ", emsg)
        sys.exit(1)
    with open(filePath, "r") as userFile:
        for line in userFile:
            userInfoLine = line.strip()
            userName, password = userInfoLine.split(":")
            users[userName] = password
    userFile.close()

    #create rooms
    for i in range(gamesCount):
        games[i] = Game(i)

    # create socket and bind
    serverPort = int(argv[1])
    
    try:
        serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serverSocket.bind( ("", serverPort) )
    except socket.error as emsg:
        print("Socket error:", emsg)
        exit(1)
    serverSocket.listen(200)
    
    print(f"The server is listening at port {serverPort}")
    global idCount
    try:
        while True:
            #create thread
            client = serverSocket.accept()
            newthd = threading.Thread(target=thd_func, args=(client, idCount, lock))
            idCount = idCount + 1
            newthd.start()
    except Exception as e:
        print("closing with exception")
        if serverSocket:
            serverSocket.close()
        sys.exit(1)


class Game:
    def __init__(self, id):
        self.reset()
    
    def reset(self):
        self.p1Went = False
        self.p2Went = False
        self.player1ID = -1
        self.player2ID = -1
        self.ready = False
        self.moves = [True, True]
        self.r = str(bool(random.getrandbits(1))).upper()
        self.id = id
        self.wins = [0, 0]
        self.count = 0
        self.closed = False
        self.p1Received = False
        self.p2Received = False
        

    def play(self, player, move):
        if player == self.player1ID:
            self.p1Went = True
            self.moves[0] = move
        else:
            self.p2Went = True
            self.moves[1] = move

    def leave(self, playerID):
        if playerID == self.player1ID:
            self.wins[0] = 0
            self.wins[1] = 1
        else:
            self.wins[0] = 1
            self.wins[1] = 0
        self.closed = True

    def getReady(self):
        return self.ready

    def bothWent(self):
        if self.closed: # handle if one or more players left
            return True
        else:
            return self.p1Went and self.p2Went

    def winner(self):
        winner = None 
        if not self.closed: # handle if one or more players left
            p1 = self.moves[0].upper()
            print("P1moves: "+p1)
            p2 = self.moves[1].upper()
            print("P2moves: "+p2)
            print("P2result: "+self.r)
            if p1 == self.r:
                self.wins[0] = 1
            if p2 == self.r:
                self.wins[1] = 1
        if self.wins[0] == 1 and self.wins[1] == 0: # player 1 wins
            winner = self.player1ID
        elif self.wins[1] == 1 and self.wins[0] == 0: # player 2 wins
            winner = self.player2ID
        else: # tie
            winner = -1

        return winner
    
    def playerCount(self):
        return self.count

    def join(self, joinPlayerID):
        if self.player1ID == -1: # if player 1 is not occupied
            self.player1ID = joinPlayerID
            self.count += 1
            return str(self.id)
        elif self.player2ID == -1: # if player 2 is not occupied
            self.player2ID = joinPlayerID
            self.count += 1
            self.ready = True
            return str(self.id)

        return str(-1) # room is full

    def bothReceived(self): # check if both players received winner info, then reset the room
        if not self.closed: 
            return self.p1Received and self.p2Received
        else:
            return True

    def received(self, playerID):
        if playerID == self.player1ID: 
            self.p1Received = True
        else:
            self.p2Received = True
            
#driver code
if __name__ == '__main__':
	if len(sys.argv) != 3:
		print("Usage: python3 GameServer.py <Server_port> \"<filepathToUserInfo.txt>\" ")
		sys.exit(1)
	main(sys.argv)