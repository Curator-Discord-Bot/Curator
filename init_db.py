import asyncio
import importlib

import config
from bot import INITIAL_EXTENSIONS
from cogs.utils.db import Table

run = asyncio.get_event_loop().run_until_complete
try:
    run(Table.create_pool(config.postgresql, min_size=5, max_size=5))
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