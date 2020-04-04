# Curator

Curator is a discord bot written by Ruukas and RJTimmerman.
It is currently early in development, and we still have many ideas that we want 
to implement. The bot is mainly developed for the Infinity Item Editor discord. 
However, we will work on having the bot run on several servers in the future.

## Requirements

- Python 3
- Python PIP
- Virtualenv
- Postgresql Database

## Setup

### Install the Dependencies

```shell
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Discord Bot Account

Have a bot account on https://discordapp.com/developers/applications

### Configuration

Fill in the configuration file _curator.conf_:

```txt
[Default]
ClientId = <client_id>
Token = <bot_token>
PostgreSQL = postgres://<username>:<password>@<server>:<port>/<database>
CommandPrefix = <command_prefix such as '!'>
```
### Initialize the database

Run `init_db.py`, in some cases you will need to run it several times, 
as some tables depend upon others.
 
## Run

```shell
python bot.py
```
