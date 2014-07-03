#!/usr/bin/env python
import sys, socket, string, pickle, operator

# server information
HOST = "irc.freenode.net"
PORT = 6667

# personal information
NICK = "bamboo"
IDENT = "bamboo"
REALNAME = "love me"
CHANNEL = "#WestfordInterns"
KARMAFILENAME = ".karmascores"

readbuffer = ""
currentusers = []
shared_source = False

# try to load the karma object
try:
    with open(KARMAFILENAME, 'rb') as file:
        karmaScores = pickle.load(file)
except:
    karmaScores = {}

# connect to the server
s=socket.socket()
s.connect((HOST, PORT))

# join the channel and set nick
s.send(bytes("NICK %s\r\n" % NICK))
s.send(bytes("USER %s %s bla :%s\r\n" % (IDENT, HOST, REALNAME)))
s.send(bytes("JOIN %s\r\n" % CHANNEL));

# returns the sender
def parseSender(line):
    return line[0][1:line[0].find("!")]

# returns the channel
def parseChannel(line):
    return line[2]

# returns the message
def parseMessage(line):
    return " ".join(line[3:])[1:].rstrip().lstrip()

# set the score for the given subject and write it to disk
def setPoints(subject, pts):
    if subject in karmaScores:
        karmaScores[subject] += pts
    else:
        karmaScores[subject] = pts
    with open(KARMAFILENAME, 'wb') as file:
        pickle.dump(karmaScores, file)

# get the score for the given subject
def getPoints(subject):
    return karmaScores[subject]

# returns the response given a sender, message, and channel
def computeResponse(sender, message, channel):

    # if the ++/-- operator is present at the end of the line
    if message[-2:] in ["++", "--", "~~"]:
        symbol = message[-2:]
        message = message[:-2].lower().rstrip().lstrip()
        
        # determine how many points to give/take
        netgain = int(symbol=="++") - int(symbol=="--")
        
        subject = message.split()
        if subject:
            subject = subject[-1]
        
        # can't give yourself karma
        if subject == sender and symbol != "~~":
            return
        
        # if it's a user, give them karma, else give points to the phrase
        if subject in currentusers:
            setPoints(subject, netgain)
            return "%s has %i karma" % (subject, getPoints(subject))
        else:
            setPoints(message.lstrip(), netgain)
            return "\"%s\" has %i point%s" % (message, getPoints(message), ["s", ""][getPoints(message)==1])

    # if the ++/-- operator is at the start, reprocess as if it were at the end
    elif message[:2] in ["++", "--"]:
        return computeResponse(sender, message[2:]+message[:2], channel)

    # display a rank for the given username
    elif message[:5] == "rank ":
        subject = message[4:].lstrip()
        return computeResponse(False, subject+"~~", channel)

    # report the top 5 users and phrases
    elif message[:5] == "ranks" or message[:6] == "scores":
        top_users = "Top 5 Users:"
        top_phrases = "Top 5 Phrases:"
        count_users = 0
        count_phrases = 0
        sorted_karma = sorted(karmaScores.iteritems(), key=operator.itemgetter(1))
        sorted_karma.reverse()
        for tup in sorted_karma:
            if tup[0] in currentusers and count_users < 5:
                top_users += " %s=%i," % tup
                count_users += 1
            elif count_phrases < 5:
                top_phrases += " \"%s\"=%i," % tup
                count_phrases += 1

        return top_users + " " + top_phrases[:-1]

    elif message == "sharesource":
        global shared_source
        if not shared_source:
            shared_source = True
            return "https://github.com/westford/bamboo/"


while 1:
    # read in lines from the socket
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    temp = readbuffer.split("\n")
    readbuffer=temp.pop()
    
    # go through each of the received lines
    for line in temp:
#        print line
        line = line.rstrip()
        line = line.split()
        
        # this is required so that the connection does not timeout
        if line[0] == "PING":
            s.send(bytes("PONG %s\r\n" % line[1]))
    
        # 353 = initial list of users in channel
        elif line[1] == "353":
            currentusers = line[6:] + [NICK]

        # update list of users currently online when new one joins
        elif line[1] == "JOIN":
            sender = parseSender(line)
            if not sender in currentusers:
                currentusers.append(parseSender(line))
        
        # this if statement responds to received messages
        elif line[1] == "PRIVMSG":
            
            # parse the information from the message
            sender = parseSender(line)
            message = parseMessage(line)
            channel = parseChannel(line)
            
            # decide what type of response to have based on the message
            response = computeResponse(sender, message, channel)

            # send the response to the channel, unless it's nothing
            if response:
                s.send(bytes("PRIVMSG %s :%s \r\n" % (CHANNEL, response)))
