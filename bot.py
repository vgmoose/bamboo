"""

    Bamboo is an IRC karma-tracking bot

    Copyright (C) 2014 Ricky Ayoub <youremail@here.com>

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

"""

#!/usr/bin/env python
import argparse
import operator
import pickle
import socket
import string
import sys

parser = argparse.ArgumentParser(description="Bamboo argument parsing")
parser.add_argument("-s", "--server", nargs='?', default="irc.freenode.net")
parser.add_argument("-p", "--port", nargs='?', default=6667, type=int)
parser.add_argument("-n", "--nick", nargs='?', default="bamboo")
parser.add_argument("-i", "--ident", nargs='?', default="bamboo")
parser.add_argument("-r", "--realname", nargs='?', default="love me")
parser.add_argument("-c", "--channel", nargs='?', default="#WestfordInterns")
parser.add_argument("-k", "--karmafile", nargs='?', default=".karmascores")
parser.add_argument("-a", "--statsfile", nargs='?', default=".stats")
parser.add_argument("-d", "--debug", action="store_true")
args = parser.parse_args(sys.argv[1:])

readbuffer = ""
currentusers = []
shared_source = False

# try to load the karma object
try:
    with open(args.karmafile, 'rb') as file:
        karmaScores = pickle.load(file)
except:
    karmaScores = {}

#try to load stats object
try:
    with open(args.statsfile, 'rb') as file:
        stats = pickle.load(file)
except:
    stats = {}

# connect to the server
s=socket.socket()
s.connect((args.server, args.port))

# join the channel and set nick
s.send(bytes("NICK %s\r\n" % args.nick))
s.send(bytes("USER %s %s bla :%s\r\n" % (args.ident, args.server, args.realname)))
s.send(bytes("JOIN %s\r\n" % args.channel));

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
    subject = subject.lower()
    if subject in karmaScores:
        karmaScores[subject] += pts
    else:
        karmaScores[subject] = pts
    with open(args.karmafile, 'wb') as file:
        pickle.dump(karmaScores, file)

# get the score for the given subject
def getPoints(subject):
    subject = subject.lower()
    return karmaScores[subject]

# set stats
def setStats(subject):
    subject = subject.lower()
    if subject in stats:
        stats[subject] += 1
    else:
        stats[subject] = 1
    with open(args.statsfile, 'wb') as file:
        pickle.dump(stats, file)

# do not engage off-channel users
def politelyDoNotEngage(sender):
    response = "[AUTO REPLY] I am not a human, apologies for any confusion."
    s.send(bytes("PRIVMSG %s :%s \r\n" % (sender, response)))

# returns the response given a sender, message, and channel
def computeResponse(sender, message, channel):
    global args

    setStats(sender)
    
    # if the ++/-- operator is present at the end of the line
    if message[-2:] in ["++", "--", "~~"]:
        symbol = message[-2:]
        message = message[:-2].rstrip().lstrip()
        
        # determine how many points to give/take
        netgain = int(symbol=="++") - int(symbol=="--")
        
        subject = message.split()
        if subject:
            subject = subject[-1]
            # Total hack solution to nullstring bug for the time being...
        else:
            subject = "" 
        
        # can't give yourself karma
        if subject == sender and symbol != "~~":
            return
        
        # if it's a user, give them karma, else give points to the phrase
        if subject.lower() in currentusers:
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
            if tup[0] not in currentusers and count_phrases < 5:
                top_phrases += " \"%s\"=%i," % tup
                count_phrases += 1

        return top_users + " " + top_phrases[:-1]

    elif message[:5] == "stats"
        top_users = "Top 5 Users by Volume:"
        count_users = 0
        sorted_stats = sorted(stats.iteritems(), key=operator.itemgetter(1))
        sorted_stats.reverse()
        for tup in sorted_stats:
            if tup[0] in currentusers and count_users < 5:
                top_users += " %s=%i," % tup
                count_users += 1
        return top_users

    elif message == "sharesource":
        global shared_source
        if not shared_source:
            shared_source = True
            return "https://github.com/vgmoose/bamboo/"

    elif message[:len(args.nick)+7] == args.nick+": /nick":
        args.nick = message[len(args.nick)+7:].lstrip().rstrip()
        s.send(bytes("NICK " + args.nick + "\r\n"))


while 1:
    # read in lines from the socket
    readbuffer = readbuffer+s.recv(1024).decode("UTF-8")
    temp = readbuffer.split("\n")
    readbuffer=temp.pop()
    
    # go through each of the received lines
    for line in temp:
        line = line.rstrip()
        line = line.split()
        
        if args.debug:
            print line

        # this is required so that the connection does not timeout
        if line[0] == "PING":
            s.send(bytes("PONG %s\r\n" % line[1]))
    
        # 353 = initial list of users in channel
        elif line[1] == "353":
            currentusers = [args.nick]
            newusers = line[6:]
            for u in newusers:
                u = u.lstrip("@").lstrip(":").lower()
                currentusers.append(u)
        
        # update list of users when a nick is changed
        elif line[1] == "NICK":
            if not line[2] in currentusers:
                currentusers.append(line[2].lstrip("@").lstrip(":").lower())
               
        elif line[1] == "433":
            args.nick = line[2]

        # update list of users currently online when new one joins
        elif line[1] == "JOIN":
            sender = parseSender(line)
            if not sender in currentusers:
                currentusers.append(parseSender(line).lstrip("@").lstrip(":").lower())
        
        # this if statement responds to received messages
        elif line[1] == "PRIVMSG":
            
            # parse the information from the message
            sender = parseSender(line)
            message = parseMessage(line)
            channel = parseChannel(line)
            
            # if not on the channel, tell the user you're a bot
            if channel != args.channel:
                politelyDoNotEngage(sender)
                continue
            
            # decide what type of response to have based on the message
            response = computeResponse(sender, message, channel)

            # send the response to the channel, unless it's nothing
            if response:
                s.send(bytes("PRIVMSG %s :%s \r\n" % (args.channel, response)))
