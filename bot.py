"""

    Bamboo is an IRC karma-tracking bot

    Copyright (C) 2014 Red Hat Westford Interns

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
# -*- coding: utf-8 -*-

import argparse
import operator
import pickle
import socket
import string
import sys
import random
import ssl
from pattern.web import *
import re

import urllib
from lxml.html import fromstring
from lxml.html import tostring
from lxml.cssselect import CSSSelector

parser = argparse.ArgumentParser(description="Bamboo argument parsing")
parser.add_argument("-s", "--server", nargs='?', default="irc.freenode.net")
parser.add_argument("-p", "--port", nargs='?', default=6667, type=int)
parser.add_argument("-n", "--nick", nargs='?', default="bamboo")
parser.add_argument("-i", "--ident", nargs='?', default="bamboo")
parser.add_argument("-r", "--realname", nargs='?', default="love me")
parser.add_argument("-c", "--channel", nargs='?', default="#DefaultChannel")
parser.add_argument("-k", "--karmafile", nargs='?', default=".karmascores")
parser.add_argument("-a", "--statsfile", nargs='?', default=".stats")
parser.add_argument("-z", "--scramblefile", nargs='?', default=".scrambles")
parser.add_argument("-q", "--quotefile", nargs='?', default=".quotes")
parser.add_argument("-l", "--msgfile", nargs='?', default=".leftmessages")
parser.add_argument("-u", "--userfile", nargs='?', default=".users")
parser.add_argument("-d", "--debug", action="store_true")
parser.add_argument("-g", "--generousfile", nargs='?', default=".generous")
parser.add_argument("-t", "--tls", action="store_true")
args = parser.parse_args(sys.argv[1:])

readbuffer = ""
currentusers = []
quotes = []
shared_source = False

def loadData(object):
    try:
        with open(object, 'rb') as file:
            return pickle.load(file)
    except:
        return {}

# load data from dumped dotfiles
karmaScores = loadData(args.karmafile)
stats = loadData(args.statsfile)
generous = loadData(args.generousfile)
scrambleTracker = loadData(args.scramblefile)
left_messages = loadData(args.msgfile)

try:
    with open(args.quotefile, 'rb') as f:
        for line in f:
            quotes.append(line)
except:
    quotes = []

try: 
    with open(args.userfile, 'rb') as f:
        for line in f:
            currentusers.append(line[:-1])
except:
    currentusers = []

# connect to the server
s = socket.socket()
if args.tls:
    s = ssl.wrap_socket(s)

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

# send to the specified user or channel
def sendTo(destination, message):
    s.send(bytes("PRIVMSG %s :%s\r\n" % (destination, message.encode("UTF-8"))))

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
    if subject in karmaScores:
        return karmaScores[subject]
    else:
        return

def toggleScrambles(subject):
    if subject in scrambleTracker:
        scrambleTracker[subject] = not scrambleTracker[subject]
    else:
        scrambleTracker[subject] = False

    with open(args.scramblefile, 'wb') as file:
        pickle.dump(scrambleTracker, file)

# set stats
def setStats(subject):
    subject = subject.lower()
    if subject in stats:
        stats[subject] += 1
    else:
        stats[subject] = 1
    with open(args.statsfile, 'wb') as file:
        pickle.dump(stats, file)

def getStats(subject):
    subject = subject.lower()
    if subject in stats:
        return stats[subject]
    else:
        return

def setGenerosity(subject, netgain):
    subject = subject.lower()
    if subject in generous:
        generous[subject] += netgain
    else:
        generous[subject] = 1
    with open(args.generousfile, 'wb') as file:
        pickle.dump(generous, file)

def getGenerosity(subject):
    subject = subject.lower()
    if subject in generous:
        return generous[subject]
    else:
        return

def getQuality(subject, stats, karma):
    if stats is None or karma is None:
        return None
    if stats != 0:
        if karma == 0:
            k = 1
        else:
            k = karma 
        
        quality = (k/float(stats)*100)
        return quality

    return 0

def scramble(tup):
    subject = tup[0]
    if subject not in scrambleTracker or scrambleTracker[subject]:
        return (subject, tup[1])
    else:
        print "Scrambled " + subject
        return (subject[:1] + "." + subject[1:], tup[1])

# do not engage off-channel users
def politelyDoNotEngage(sender):
    response = "[AUTO REPLY] I am not a human, apologies for any confusion."
    sendTo(sender, response)

def helpMessage(sender):
    response = "README can be found here: https://github.com/vgmoose/bamboo"
    sendTo(sender, response)

def quoteMessage(sender, message):

    if message == "" or message.split(' ') == []:
        return

    message = message[1:]
    try:
        message.encode("ascii")
    except:
        return "no thank you :("
    if message.isdigit():
        anonSay("I think you want .getquote "+message)
        qu = specificQuote(message)
        return qu
    quotes.append(message)

    with open(args.quotefile, 'a') as f:
        f.write(quotes[len(quotes)-1] + '\n')

    response = "Quote #" + str(len(quotes)) + " added by " + sender
    sendTo(args.channel, response)

def anonSay(message):
    print message
    sendTo(args.channel, message)

def anonDo(message):
    s.send('PRIVMSG ' + args.channel + ' :\x01ACTION ' + message + '\x01\n')

# depends on git pull in shell while loop
def updateBamboo():
    exit(0)

def xkcd(searchTerm):
    if searchTerm != "":
        g = Google()
        for result in g.search("xkcd"+searchTerm):
            if "http://xkcd.com/" in result.url:
                return result.url

def youtube(searchTerm):
    if searchTerm != "":
        g = Google()
        for result in g.search("youtube"+searchTerm):
            if "http://www.youtube.com/watch" in result.url:
                return result.title + " " + result.url

def specificQuote(num):
    try: 
        n = int(num) - 1
        if len(quotes) > n:
            return quotes[n]
    except:
        # look for the search contents
        matchedquotes = []
        for quote in quotes:
            if num.lower() in quote.lower():
                matchedquotes.append(quote)
        if len(matchedquotes) > 0:
            return matchedquotes[random.randint(0, len(matchedquotes)-1)]

def randomQuote():
    return quotes[random.randint(0, len(quotes)-1)]

def deliver_any_messages(target):
    target = target.lower()
    if target in left_messages:
        msgs = left_messages[target]
        for msg in msgs:
            anonSay(target+": <"+msg[0]+"> "+msg[1])
        del left_messages[target]

        with open(args.msgfile, 'wb') as file:
            pickle.dump(left_messages, file)

# returns the response given a sender, message, and channel
def computeResponse(sender, message, channel):
    global args
    splitmsg = message.split(' ')
    func = splitmsg[0].lower()

    if sender:
        setStats(sender)
        deliver_any_messages(sender)

    # if the ++/-- operator is present at the end of the line
    if message[-2:] in ["++", "--"] and message.upper().find("C++") < 0:
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

        if symbol == "``":
            usrstats = getStats(subject)
            if usrstats:
                return "%s has sent %i messages" % (subject, usrstats)
            else:
                return "%s is not a recorded user" % subject 

        if symbol == "**":
            usrstats = getStats(subject)
            usrkarma = getPoints(subject)
            usrquality = getQuality(subject, usrstats, usrkarma)
            if usrquality:
                return "%s has %.2f%% quality posts"  % (subject, usrquality)
            else:
                return "%s has no stats or karma recorded" % subject

        if symbol == "$$":
            usrgener = getGenerosity(subject)
            if usrgener:
                return "%s has given %i net karma" % (subject, usrgener)
            else:
                return "%s has never used karma" % subject            

        # can't give yourself karma
        if subject.lower() == sender.lower() and symbol != "~~":
            return
        
        # if it's a user, give them karma, else give points to the phrase
        if subject.lower() in currentusers:
            setPoints(subject, netgain)
            setGenerosity(sender, netgain)
            return "%s has %i karma" % (subject, getPoints(subject))
        else:
            setPoints(message.lstrip(), netgain)
            return 
            #return "\"%s\" has %i point%s" % (message, getPoints(message), ["s", ""][getPoints(message)==1])

    # if the ++/-- operator is at the start, reprocess as if it were at the end
    elif message[:2] in ["++", "--"]:
        return computeResponse(sender, message[2:]+message[:2], channel)


    # display a rank for the given username
    elif func == "rank":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"~~", channel)

    # report the top 5 users and phrases
    elif func == "ranks" or func == "scores":
        if len(splitmsg) == 1:
            top_users = "Top 5 Users:"
            top_phrases = "Top 5 Phrases:"
            count_users = 0
            count_phrases = 0
            sorted_karma = sorted(karmaScores.iteritems(), key=operator.itemgetter(1))
            sorted_karma.reverse()
            for tup in sorted_karma:
                if tup[0] in currentusers and count_users < 5:
                    top_users += " %s=%i," % scramble(tup)
                    count_users += 1
                if tup[0] not in currentusers and count_phrases < 5:
                    top_phrases += " \"%s\"=%i," % scramble(tup)
                    count_phrases += 1

            return [top_users[:-1], top_phrases[:-1]]

    elif func.startswith("https://twitter.com/"):
        try:
            url = func
            content = urllib.urlopen(url).read()
            doc = fromstring(content)
            doc.make_links_absolute(url)
            
            name_sel = CSSSelector(".permalink-tweet .username")
            text_sel = CSSSelector(".permalink-tweet .tweet-text")
            
            regex = re.compile("[<].*?[>]")
            
            username = re.sub(regex, "", tostring(name_sel(doc)[0])).strip()
            tweet = re.sub(regex, "", tostring(text_sel(doc)[0])).strip()

            tweet = tweet.replace("pic.twitter", " pic.twitter")

            return "<"+username+"> "+tweet

        except:
            pass


    elif func == ".listquotes" or func == ".listquote":
        counter = 0
        allquotes = ""
        subquotes = quotes
        total_quotes = len(quotes)
        if total_quotes > 5:
            counter = total_quotes - 5
            subquotes = quotes[total_quotes-5:]
        sendTo(sender, "Here are the last 5 quotes:")

        for quote in subquotes:
            counter += 1
            sendTo(sender, str(counter)+": "+quote.rstrip("\n") )
            #allquotes += str(counter)+": "+quote.rstrip("\n") + "  /   "
        # goo 400 at a time
       # allquotes = allquotes[:-5]
       # for x in range(0, len(allquotes), 400):
       #     sendTo(sender, allquotes[x:x+400])

        sendTo(sender, "and here's all of 'em: http://wiiu.vgmoose.com/quotes.txt")

        return "sent all quotes to " + sender + "!"

    elif func == "stats":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"``", channel)
        elif len(splitmsg) == 1:
            top_users = "Top 5 Users by Volume:"
            count_users = 0
            sorted_stats = sorted(stats.iteritems(), key=operator.itemgetter(1))
            sorted_stats.reverse()
            for tup in sorted_stats:
                if tup[0] in currentusers and count_users < 5:
                    top_users += " %s=%i," % scramble(tup)
                    count_users += 1
            return top_users[:-1]

    elif func == "morestats":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"``", channel)
        elif len(splitmsg) == 1:
            top_users = "Top 10 Users by Volume:"
            count_users = 0
            sorted_stats = sorted(stats.iteritems(), key=operator.itemgetter(1))
            sorted_stats.reverse()
            for tup in sorted_stats:
                if tup[0] in currentusers and count_users < 10:
                    top_users += " %s=%i," % scramble(tup)
                    count_users += 1
            return top_users[:-1]

    elif func == "generosity":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"$$", channel)
        elif len(splitmsg) == 1:
            most_generous = "Top 5 Most Generous Users:"
            most_stingy = "Top 5 Stingiest Users:"
            count_gen = 0
            count_sting = 0
            sorted_gen = sorted(generous.iteritems(), key=operator.itemgetter(1))
            sorted_gen.reverse()
            for tup in sorted_gen:
                if tup[0] in currentusers and count_gen < 5:
                    most_generous += " %s=%i," % scramble(tup)
                    count_gen += 1
            sorted_gen.reverse()
            for tup in sorted_gen:
                if tup[0] in currentusers and count_sting < 5:
                    most_stingy += " %s=%i," % scramble(tup)
                    count_sting += 1
            return [most_generous[:-1], most_stingy[:-1]]

    elif func == "quality":
        if len(splitmsg) == 2:
            subject = splitmsg[1].lstrip()
            return computeResponse(sender, subject+"**", channel)
        if len(splitmsg) == 1:
            top_users = "Top 5 Users by Quality:"
            spam_users = "The Round Table of Spamalot:"
            count_users = 0
            sorted_quality = {}
            sorted_stats = sorted(stats.iteritems(), key=operator.itemgetter(0))
            sorted_karma = sorted(karmaScores.iteritems(), key=operator.itemgetter(0))
            for stats_tup in sorted_stats:
                for karma_tup in sorted_karma:
                    if stats_tup[0] == karma_tup[0] and karma_tup[0] in currentusers:
                        sorted_quality[stats_tup[0]] = \
                        getQuality(stats_tup[0], stats_tup[1], karma_tup[1])
        
            sorted_quality = sorted(sorted_quality.iteritems(), key=operator.itemgetter(1))
            sorted_quality.reverse() 
            for tup in sorted_quality:
                if count_users < 5:
                    top_users += " %s=%.2f%%," % scramble(tup)
                    count_users += 1 
            count_users = 0
            sorted_quality.reverse() 
            for tup in sorted_quality:
                if count_users < 5:
                    spam_users += " %s=%.2f%%," % scramble(tup)
                    count_users += 1
            return [top_users[:-1], spam_users[:-1]]

    elif func == ".xkcd":
        return xkcd(message[5:])

    elif func == ".yt":
        return youtube(message[3:])
        
    elif message == "sharesource":
        global shared_source
        if not shared_source:
            shared_source = True
        return "https://github.com/vgmoose/bamboo/"

    elif message[:len(args.nick)+10] == args.nick+": scramble":
        toggleScrambles(sender)
        return sender + " is now known as %s%s" % scramble((sender,""))

    elif message[:len(args.nick)+8] == args.nick+": update":
        updateBamboo()

    elif message[:len(args.nick)+7] == args.nick+": /nick":
        args.nick = message[len(args.nick)+7:].lstrip().rstrip()
        s.send(bytes("NICK " + args.nick + "\r\n"))

    elif func == ".quote":
        return quoteMessage(sender, message[6:])

    elif func == ".getquote":
        spltmsg = message.split(' ')
        if len(spltmsg) > 1:
            return specificQuote(spltmsg[1])
        return randomQuote()

    elif func == "tell" or func == ".tell":
        splitmsg = message.split(' ')
        if len(splitmsg) > 2:
           splitmsg[1] = splitmsg[1].lower()
           if splitmsg[1] not in left_messages:
               left_messages[splitmsg[1]] = []
           left_messages[splitmsg[1]].append((sender, " ".join(splitmsg[2:])))

        with open(args.msgfile, 'wb') as file:
            pickle.dump(left_messages, file)

        return "will notify "+splitmsg[1]+" when they sign on or send a message"

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
            if not args.nick in currentusers:
                currentusers.append(args.nick)
            newusers = line[6:]
            for u in newusers:
                u = u.lstrip("@").lstrip(":").lower()
                if u[0] == "+":
                    u = u[1:]
                if not u in currentusers:
                    currentusers.append(u)
                    with open(args.userfile, 'a') as f:
                        f.write(u + '\n')
            deliver_any_messages(args.nick)
        


        # update list of users when a nick is changed
        elif line[1] == "NICK":
            u = line[2].lstrip("@").lstrip(":").lower()
            if not line[2] in currentusers:
                if u[0] == "+":
                    u = u[1:]
                if not u in currentusers:
                    currentusers.append(u)
                    with open(args.userfile, 'a') as f:
                        f.write(u + '\n')
            deliver_any_messages(u)

        elif line[1] == "KICK":
            # rejoin when kicked
            s.send(bytes("JOIN %s\r\n" % args.channel));
               
        elif line[1] == "433":
            args.nick = line[2]

        # update list of users currently online when new one joins
        elif line[1] == "JOIN":
            u = parseSender(line).lstrip("@").lstrip(":").lower()
            if not u in currentusers:
                currentusers.append(u)
                with open(args.userfile, 'a') as f:
                    f.write(u + '\n')
            deliver_any_messages(u)
        
        # this if statement responds to received messages
        elif line[1] == "PRIVMSG":
            
            # parse the information from the message
            sender = parseSender(line)
            message = parseMessage(line)
            channel = parseChannel(line)
            
            # if not on the channel, tell the user you're a bot
            if channel != args.channel:
                splitmsg =message.split(' ')
                func = splitmsg[0]
                arglist = splitmsg[1:]
 

                if func == "update":
                    updateBamboo()

                elif func == "say" and arglist != []:
                    anonSay(' '.join(arglist))

                elif func == "action" and modflag and arglist != []:
                    anonDo(' '.join(arglist))

                elif func == "help":
                    helpMessage(sender)

                elif func == "quote" and arglist !=[]:
                    quoteMessage(sender, ' '+' '.join(arglist))

                else:
                    politelyDoNotEngage(sender)
                continue

            
            # decide what type of response to have based on the message
            response = computeResponse(sender, message, channel)

            # send the response to the channel, unless it's nothing
            if response:
                if type(response) is not list:
                    response = [response]
                
                # send each string in returned array
                for line in response:
                    sendTo(args.channel, line)
