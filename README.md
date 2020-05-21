# Curator

Curator is a discord bot written by Ruukas and RJTimmerman.
It is currently early in development, and we still have many ideas that we want 
to implement. The bot is mainly developed for the Infinity Item Editor discord. 
However, we will work on having the bot run on several servers in the future.

## Requirements

- **Python 3** ([Windows Download](https://www.python.org/downloads/). Linux: `sudo apt install python3`)
- **Python PIP** (Included in Windows python installer. Linux: `sudo apt install python3-pip`)
- **Virtualenv** (included in Windows python installer. Linux: `sudo pip3 install virtualenv`)
- **PostgreSQL Database** ([Download](https://www.postgresql.org/download/) or setup for free on [ElephantSQL](https://www.elephantsql.com/))

## Setup

### Install the Dependencies

#### Windows:
```bat
python -m venv venv
CALL venv/Scripts/activate.bat
pip install -r requirements.txt
```

#### Linux:
```shell
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Discord Bot Account

Have a bot account on [Discord Developer Portal](https://discordapp.com/developers/applications).

### Configuration

Create a file called `curator.conf` and fill in the credentials:

```txt
[Default]
# Client ID from 'General Information' tab of your Discord Application
ClientId=<client_id>
# Token from 'Bot' tab of your Discord Application
Token=<bot_token>
# PostgreSQL URI to connect to a database the bot can use
PostgreSQL=postgres://<username>:<password>@<server>:<port>/<database>
# The size of the pool, the bot will use to communicate with the database
PoolSize=3
# The prefix that the bot will use for commands such as !help
CommandPrefix=!
# The id of the channel used to forward received DMs to
DMDump=<channel_id>
```

### Initialize the database

Run `init_db.py`, in some cases you will need to run it several times, 
as some tables depend upon others.
 
## Run
*Linux users might need to replace `python` with `python3`.*
```shell
python bot.py
```

## Contact
If you have any questions, or would like to discuss the bot, you can find me on Discord: `Ruukas#9050`.
