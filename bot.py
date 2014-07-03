#!/usr/bin/env python

import sys
import socket
import pickle
import string
 
HOST = "irc.lab.bos.redhat.com"
PORT = 6667
 
NICK = "bamboo"
IDENT = "bamboo"
REALNAME = "bamboo"
channel = "#WestfordInterns"
 
readbuffer = ""
 
s=socket.socket( )
s.connect((HOST, PORT))
 
s.send(bytes("NICK %s\r\n" % NICK))
s.send(bytes("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME)))
s.send(bytes("JOIN %s\r\n" % (channel)));

kscorefile = ".karmascores"

try:
    with open(kscorefile, 'rb') as handle:
        score = pickle.load(handle)
except:
    score = {}
 
while 1:
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    temp = readbuffer.split("\n")
    readbuffer=temp.pop( )
 
    for line in temp:
        line = line.rstrip()
        line = line.split()
 
        if(line[0] == "PING"):
            s.send(bytes("PONG %s\r\n" % line[1]))
        if(line[1] == "PRIVMSG"):
            sender = ""
            for char in line[0]:
                if(char == "!"):
                    break
                if(char != ":"):
                    sender += char 
            size = len(line)
            i = 3
            message = ""
            while(i < size): 
                message += line[i] + " "
                i = i + 1
            message = message.lstrip(":").rstrip(" ")
            name = message[:-2]
            sym = message[-2:]
            if name == sender or (sym != "++" and sym != "--"):
                continue
            if name not in score:
                score[name] = 0
            score[name] += (sym=="++")
            score[name] -= (sym=="--")
            with open(kscorefile, 'wb') as handle:
                pickle.dump(score, handle)
            s.send(bytes("PRIVMSG %s :%s has %i karma\r\n" % (channel, name, score[name])))

        for index, i in enumerate(line):
            print(line[index])
