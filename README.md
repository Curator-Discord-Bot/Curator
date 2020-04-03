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

## Install Dependencies

```shell
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running the bot
 - Install dependencies
 - Create `config.py`:
   ```python
   client_id = '<client_id>'
   token = '<bot_token>'
   postgresql = 'postgres://<username>:<password>@<server>:<port>/<database>'
   command_prefix = '<command_prefix such as '!'>'
   ```
 - Initialize the database by running `init_db.py`, in some cases you will need to run it several times, as some tables depend upon others.
 - Run the bot by running `bot.py`

