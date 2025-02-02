# Team-SK Major Group Project

## Team members
The members of the team are:
* Fahad AlAbdulrazzaq
* Saleh AlSubaie
* Shaikha AlYahya
* Mohammed Abdullah
* Ali Fakhroo
* Pranav Subash
* Yasir Kabir Sattar
* Ricky Gordon

## Project structure
The project is called `ticketing_system`. It currently consists of a single app `ticket`

## Deployed version of the application
[Add deployment information when available]

## Installation instructions
To install the software and use it in your local development environment, you must first set up and activate a local development environment. From the root of the project:

```bash
$ virtualenv venv
$ source venv/bin/activate
```

Install all required packages:

```bash
$ pip3 install -r requirements.txt
```

Migrate the database:

```bash
$ python3 manage.py migrate
```

Run all tests with:

```bash
$ python3 manage.py test
```

## Sources
The packages used by this application are specified in the `requirements.txt` file
