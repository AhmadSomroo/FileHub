# FileHub
A python based secure File Web-Based File Sharing App
In the project, the app runs on port 5000 with Apache2.0 server as reverse proxy between client and app.
Although every vulnerability was addressed to best possible way but, 
the app might still be vulnerable to CSRF as some security testing utilities gave only CSRF vulnerability in this App.

- Server side still needs to be protected as the database is SQL and unencrypted. This database should be appropriate for the usecase.
- Database still contains dummy enteries but some of them will not work because the database also contains the data of files which are obviously not present.

## Project Overview
![Overview](image/view.png)
