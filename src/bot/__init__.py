import asyncio
import logging
import os

if os.name == "nt":
    # Change the event loop policy on Windows to avoid exceptions on exit
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Some basic logging to get existing loggers to show
logging.getLogger().addHandler(logging.StreamHandler())
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("discord").setLevel(logging.INFO)
