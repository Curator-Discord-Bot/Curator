import asyncio
import importlib

from bot import get_config, INITIAL_EXTENSIONS
from cogs.utils.db import Table

config = get_config()

run = asyncio.get_event_loop().run_until_complete
try:
    run(Table.create_pool(config['postgresql'], command_timeout=60, min_size=config['poolsize'], max_size=config['poolsize']))
except Exception as e:
    print(e)
    print('Could not set up PostgreSQL. Exiting.')
    exit()

cogs = INITIAL_EXTENSIONS
for ext in cogs:
    try:
        importlib.import_module(ext)
    except Exception as e:
        print(f'Could not load {ext}.\n{e}')
        exit()

for table in Table.all_tables():
    try:
        created = run(table.create(verbose=True, run_migrations=False))
    except Exception as e:
        print(f'Could not create {table.__tablename__}.\n{e}')
    else:
        if created:
            print(f'[{table.__module__}] Created {table.__tablename__}.')
        else:
            print(f'[{table.__module__}] No work needed for {table.__tablename__}.')