DESIGN.md

# Main idea
Yepop was inspired by [https://vinted.com/](https://) and [https://www.depop.com/](https://), two online marketplaces for exchanging clothes. I’ve bought the entirety of my clothes on Vinted and Depop for years now, so I thought it would be interesting to implement a version for Yale students and really understand what happens behind the scenes. The format most appropriate to implement this project seemed to be a web-based application using Python, SQL, HTML, CSS, flask and jinja.

# Back-end
**SQL**
Before beginning to code, implementing a solid database was crucial. This comprised of creating the four following tables:
* Users: unique integer ids for each user (id, primary key), a unique username for each user (username), the user’s email (email), the user’s phone number (phone), the hashed password for the account (hash)
    * Used to identify user sessions with the “login.html” and “register.html” files
    * Makes it possible to put in contact two users who have claimed/sold items in the “messages.html” page

* Items: unique id for each item (item_id), a unique user id that identifies the seller (seller_id, refers to users “id”), a name (name), a photo (photo), a category (category), a condition (condition), a size (size), a color (color)
    * Stores the information on all of the items that are up for sale. Items are added to the database through the “sell” page.
    * The different characteristics of the item are what make it possible to search for items.

* Transactions: a unique transaction_id for each claim/sell (transaction_id), a unique user id that identifies the item (item_id, refers to items “item_id”), a unique user id that identifies the seller (seller_id, refers to users “id”), a unique user id that identifies the claimer (claimer_id, refers to users “id”), the date of the transaction (date), the name of the item (item)
    * This table is what makes it possible to format messages (know who has claimed an item vs. who has sold one). It’s also a way of having proof of the exchange that should be taking place between two users

* Messages: a unique id for each message (message_id, primary key), a unique id for the sender (sender, refers to users “id”), a unique id for the receiver (receiver, refers to users “id”), the content of the message (content), the id of the transaction the message is referring to or 0 if the message does not refer to a transaction (transaction_id, refers to transactions “transaction_id)
    * This table is what makes it possible to have a “messages” page and put two users in contact. There are two ways that items are added to the table: first of all, any time a transaction is made, a message is added into the table directly in the Python file. Messages are also added to the database when you send a message to a user the through the messages.html file.


**Python and Flask**
The app routes in the “app.py” file were implemented in the following order:
* /login
    * [GET]: renders the template for the login page
    * [POST]: retrieves the user’s information from the form, checks that login information is correct, remembers the user’s session, lets the user access the rest of the website
    * Sourced from Problem Set 9

* /logout
    * Clears the user’s session and redirects user to the main page (which requires you to login)
    * Sourced from Problem Set 9
* /register
    * [GET]: displays the register form
    * [POST]: retrieves data from form, checks that the input is correct, inserts the information in the “users” table and logs the user in
* /sell
    * [GET]: displays the form to upload an item
    * [POST]: retrieves the user’s input (no need to check if the fields have been filled in because I use the “required” attribute in the input), add the item to the database, redirect to a template that notifies you that the upload was successful
    * This is the first route from the inside of the website that I decided to implement because all the other routes refer to the items table, so I needed to have the ability to populate it
* /search
    * [GET]: displays the form to search an item
    * [POST]: retrieves the user’s input, queries the database for such items, formats list of items, renders “searched” template
    * The search route had to be implemented after the sell route because they are so similar (similar html form to search). I also needed to have a populated database to be able to search. The difficulty here was formatting the list of dictionaries of items in order to then display them in a sort of grid layout. For this I decided to split the list of dictionaries in smaller lists of three items. 
* /claim
    * This route has to be implemented right after the “search route” because it uses the form that is in the “searched” page. 
    * It retrieves the information from the form (item id, seller_id, user_id), add the item to the transaction table, deletes it from the items database and inserts a message in both the claimer’s and the seller’s inbox, renders the “success” template. This route was essentially a lot of SQL queries. 
* /messages
    * Queries through the database for messages whose “receiver” is the logged in user then renders the “messages” template. 
    * Relatively easy to implement. This query route just necessitated a database query. The more difficult part was in finding the usernames of the senders and inserting them into the correct dictionary and in formatting the html. This however was made much easier by using some bootstrap attributes.
* /message
    * Retrieves the information about the sender, receiver, content, checks if the username exists (redirects to the messages page if it does not), inserts the message in the database.
    * What was most difficult in this route was especially the front-end part of the source code. I had a lot of trouble making the modal work correctly.
* /myitems
    * Very similar to the “/” route except that it queries the database according to the user’s id. Formats the list of items and renders the”myitems” template. 
* /delete
    * Had to be implemented after the “myitems” route as this route refers to the “delete” button in the “myitems” page. 
    * Retrieves information from the form in the modal and deletes the item from the items database. 

In the “helpers.py” file the only function implemented was “login_required”. It checks if a user has logged in to give them access to most of the pages of the website. If the user hasn’t logged in it redirects the user to the login page. (Sourced from Problem Set 9)

# Front-end
Yepop is comprised 10 templates files and 3 static files. The three static files are styles.css (which controls the style of the site), favicon.ico (the logo of the website), and write.png (the icon to write a message). All of the templates, thanks to jinja, are customizable.
* layout.html
    * Sets the layout for the entire web app. This page contains the bootstrap links and the navbar.
    * This file makes it possible to maintain a consistent interface without having to write starter code at the beginning of each HTML template. 
* index.html
    * Displays the items up for sale using a bootstrap grid system. It also contains bootstrap modals that make it possible claim an item. 
* register.html & login.html
    * HTML templates for displaying the registration form and the login form. Both of these pages use bootstrap attributes to format the select inputs. 
* messages.html
    * Displays a table containing the messages received by the logged in user.
    * I had a lot of trouble making an image into a button on this page. The image would not superimpose correctly with the button container. In the end, I was able to make it look clean by having the button container inherit the background-color of the rest of the page. 
* myitems.html
    * Displays a grid of the items uploaded by the logged in user.
* search.html
    * Form to search for an item
* searched.html
    * Displays a grid of the items with the same characteristics as what was inputted in the search form
* sell.html
    * Form to sell an item 
* success.html
    * Template to display a success message for successful claiming or uploading of an item. 


