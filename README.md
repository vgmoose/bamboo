Bamboo is an IRC bot that tracks karma of users.

It is currently named after the nearby [bamboo restaurant](http://www.yelp.com/biz/bamboo-fine-asian-cuisine-westford), which contrasts with the also nearby [karma restaurant](http://karmawestford.com/).

Functionality:

Karma is awarded to users that are presently in the channel. Points can also be awarded to phrases. The differences between the two primarily revolve around the fact that if the object directly to the left of the operator (++/--) is a user, then only the user will be awarded points, whereas phrases can be separated by spaces and the entire word will be awarded points.

Incrementing Karma (User)
- [user]++
- any arbitrary words [user]++
*result: [user] will get +1 karma*

Incrementing Points (Phrase)
- any atribitrary words++
*result: "any aribtrary words" will get +1 point*

Decrementing karma (User
- [user]--
- any arbitrary words [user]--
*result: [user] will get -1 karma*

Decrementing karma (Phrase)
- any atribitrary words--
*result: "any aribtrary words" will get -1 point*

Checking rank
- rank [user]
- ranks
- [user]~~
*result: information on the top 5 users and phrases*
