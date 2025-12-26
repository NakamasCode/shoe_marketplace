# shoe_marketplace


#### Video Demo:  [https://youtu.be/6614llIEWio?si=WTqAnf1XYxe_C3WH]

#### Description:
This project is a web-based application built as my CS50 final project. Its purpose is to address the challenge artisans and craftsmen face when they have quality products but no digital marketplace to showcase them. The solution lets users select roles—either buyer or seller. Sellers can add products, manage categories, and receive inquiries from potential buyers through an inbox system. The application prioritizes user experience, leveraging insights I gained from a Balsamiq interface design course to make it intuitive and straightforward. Buyers can explore multiple sellers and their products, make inquiries, or complete purchases easily.


The project is implemented using Flask as the backend framework, with Jinja templates for HTML and Bootstrap for CSS and page styling for the frontend interface. It uses a relational database to store user data and application records securely. User authentication is included to ensure that each user can only access their own information, and core CRUD (Create, Read, Update, Delete) functionality is implemented throughout the application.

This project reflects my understanding of core CS50 concepts such as programming logic, data persistence, user input validation, and web application structure.

---

### Project Overview

The application allows users to create a profile, add products, upload a gallery showcasing their workspace, send messages regards to products. A typical user can register an account, log in, and interact with the system through a clean and simple interface based on the role selected. Once logged in, users are able to [list main features: add products, update them, view messages, delete entries,preview of product etc.].

One of the main goals of this project was to keep the interface simple while still providing meaningful functionality. Rather than adding unnecessary complexity, I focused on ensuring that each feature worked reliably and logically.

---

### File Structure and Functionality
### Project Structure

The project consists of several files and folders, each serving a specific purpose:

- **app/__init__.py**  
  Initializes the Flask application. Sets up the app instance, configures extensions like the database and login manager, and registers routes and blueprints.

- **app/routes.py**  
  Defines all application routes and associated logic. Handles HTTP requests, user interactions, and connects frontend templates to backend functionality.

- **app/models.py**  
  Defines the database models. Structures how data such as users, sellers, buyers, and product records are organized, ensuring consistency and easier database management.

- **app/forms.py**  
  Contains web forms used throughout the application. Includes validation to ensure users submit complete and correct data, for actions like registration, login, and product management.

- **app/templates/**  
  Contains HTML templates for rendering pages. Includes login, registration, dashboard, and product listing pages. Jinja templating is used to dynamically display content.

- **app/static/**  
  Contains static assets such as CSS, images, and JavaScript, ensuring a clean, consistent, and user-friendly interface.

- **migrations/**  
  Stores database migration files used to manage schema changes over time. Enables the application to safely evolve its database structure without losing data.

- **shoemart.py**  
  The main entry point of the application. Running this file starts the Flask server and launches the web app.

- **config.py**  
  Contains configuration settings for the application, such as database URIs, secret keys, and other environment-specific settings.

---
### Design Decisions

Flask was chosen for its lightweight and flexible nature, ideal for small to medium web applications. SQLite was used for simplicity and adequacy at this scale.

Before building the frontend with Bootstrap, I wireframed the site in Balsamiq. This allowed me to plan layout and user experience, making the interface intuitive and reducing redesigns. User authentication ensures privacy and security, with passwords securely hashed. The frontend was intentionally kept minimal, focusing on functionality and clarity to maintain stability and ease of use.


---
### Challenges and Lessons Learned

One of the main challenges during development was structuring the application correctly and managing how data flows between the backend and frontend. Another significant challenge was deploying the project from a local environment to a live server on Render. To handle image storage without running into hosting limitations, I switched to using Cloudinary on a free-tier account, which allowed the application to manage media efficiently in production.

This project reinforced important programming concepts such as problem decomposition, testing features incrementally, and writing readable, maintainable code. It also improved my confidence in building full-stack applications from scratch and preparing them for real-world deployment.

---

### Conclusion

This project represents the culmination of my learning in CS50. It demonstrates my ability to design, implement, and document a functional software project. While there are areas that could be expanded in the future, the current version successfully achieves its intended purpose and serves as a solid foundation for further development.
