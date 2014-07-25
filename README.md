## Bamboo

Bamboo is an IRC bot that tracks karma of users.

It is currently named after the nearby [bamboo restaurant](http://www.yelp.com/biz/bamboo-fine-asian-cuisine-westford), which contrasts with the also nearby [karma restaurant](http://karmawestford.com/).

### Debugging

To run Bamboo in debug mode, the following syntax is recommended:
```
python bot.py -n "uniqueusername" -c "#uniquechannel" -d
```

And the bot will join #uniquechannel as uniqueusername on freenode. All messages received will be printed to the terminal.

The ```argparse``` module will also be required, which can be installed via pip:
```
pip install argparse
```

### Contributing

All pull requests for anything at all are welcome. Bamboo is the product of its creators. To increase the likelihood of your branch being merged, please try to ensure that it is based off master, and GitHub gives it the "ready to merge" status.


### Functionality

#### Ranking

Karma is awarded to users that are presently in the channel. Points can also be awarded to phrases. The differences between the two primarily revolve around the fact that if the object directly to the left of the operator (++/--) is a user, then only the user will be awarded points, whereas phrases can be separated by spaces and the entire word will be awarded points.

Incrementing Karma (User)
- [user]++
- any arbitrary words [user]++

*result: [user] will get +1 karma*

Incrementing Points (Phrase)
- any arbitrary words++

*result: "any arbitrary words" will get +1 point*

Checking karma/points rank
- rank [user]
- [user]~~
- ranks

*result: information on the top 5 users and phrases*

#### Channel Stats

Stats are kept track of for each user that sends messages to the channel. That is, every time a user speaks a counter specifically for them is incremented. This keeps track of who is speaking the most in the channel. 

Checking stats
- stats

*result: information about the top 5 speakers in the channel*

#### Quality

Quality is calculated by dividing the number of times a user speaks by their rank. This gives a metric for the "quality" of a user's posts (i.e. what percent of them are "good")

Checking quality
- quality

#### Generosity

Generosity tracks which users are giving the most karma using the ++ commands. Every time a user issues such a command, their generosity value increases. This information will give a metric of who is using the system the most to increase other user's karma.

Checking generosity
- generosity

