# Item catalog
The Item Catalog project consists of developing an application that provides a list of items within a variety of categories, as well as provide a user registration and authentication.

 - Selecting a specific category shows you all the items available for that category.
 - Selecting a specific item shows you specific information of that item.
 - After logging in, a user has the ability to add, update, or delete item info.
 - The application provides a JSON endpoint.
 
 ## Json End_points
 tha app provide json end points in many forms:
 - {{host}}/items/json >> to display all items
 - {{host}}/category/<int:id>/JSON >> to view a category of items by its id
 - {{host}}/item/<int:id>/JSON >> to view an item by its id
 
 ## Installing
 for ubuntu run command :
  - sudo apt-get install imagemagick
 ### For the app to work you must run commands:
 - pip install -r requirements.txt
 ### to setup database you must run commands:
 - python database_setup.py
 - python add_main_category.py
 ### finally to run the app :
 - python app.py
 