# Aurion
This repo is for ENSAIT students (or every other school that uses Aurion?) to receive notifications about modified/added/removed classes.
It connects to aurion, parses the classes, then writes them to a csv file. At the next launch, the old file will be compared to the new one to check for modifications. It will then send a notification by SMS.
For this to work, you need to create a credentials.py file at the repo's root containing your login and your password, formatted like this:
```
login = "username"
password = "password"
```
