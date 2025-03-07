#!/usr/bin/env python3
#
# Description:  List all Unmatched and Incorrectly matched files.
# Author:       https://github.com/Rycochet
# Requires:     plexapi, python_dotenv, schedule
#
# Config via a .env file, PLEX_TOKEN, PLEX_URL (optional), PLEX_PATH<n> + PLEX_PATH<n>_REPLACE

import logging
import os
import schedule
import sys

from dotenv import load_dotenv
from glob import glob
from plexapi.server import PlexServer
from time import sleep

load_dotenv()

LABEL = "FixMatch"
TRUTHY = ["true", "1", "yes"]
isTTY = sys.stdout.isatty()

PLEX_TOKEN = os.getenv("PLEX_TOKEN")
PLEX_TOKEN_FILE = os.getenv("PLEX_TOKEN_FILE")
if PLEX_TOKEN_FILE:
    with open(PLEX_TOKEN_FILE) as f: PLEX_TOKEN = f.read().strip()
PLEX_URL = os.getenv("PLEX_URL", "http://localhost:32400")

LOG_LEVEL = os.getenv("LOG_LEVEL", "DEBUG").upper()

CHECK_ADD_LABEL = os.getenv("CHECK_ADD_LABEL", "true").lower() in TRUTHY
CHECK_UNMATCH = os.getenv("CHECK_UNMATCH", "true").lower() in TRUTHY
CHECK_NOW = os.getenv("CHECK_NOW", "true" if isTTY else "false").lower() in TRUTHY
CHECK_AT = [checkTime.strip() for checkTime in os.getenv("CHECK_AT", "06:30").split(",")]
CHECK_AGENTS = [agent.strip() for agent in os.getenv("CHECK_AGENTS", "tvdb,tmdb,imdb").split(",")]
CHECK_LIBRARY = [library.strip() for library in os.getenv("CHECK_LIBRARY", "*").lower().split(",")]

CHECK_PATHS = {}
for i in range(9):
    if os.getenv(f'CHECK_PATH{i}') and os.getenv(f'CHECK_PATH{i}_REPLACE'):
        CHECK_PATHS[os.getenv(f'CHECK_PATH{i}')] = os.getenv(f'CHECK_PATH{i}_REPLACE')

logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

if LOG_LEVEL == "DEBUG":
    logger.setLevel(logging.DEBUG)
elif LOG_LEVEL == "INFO":
    logger.setLevel(logging.INFO)
elif LOG_LEVEL == "WARN" or LOG_LEVEL == "WARNING":
    logger.setLevel(logging.WARNING)
elif LOG_LEVEL == "ERROR":
    logger.setLevel(logging.ERROR)

if not PLEX_TOKEN:
    logger.error("Error: You must supply a PLEX_TOKEN or PLEX_TOKEN_FILE env variable.")
    sys.exit(-1)

if not CHECK_AT and not CHECK_NOW:
    logger.error("Error: Either CHECK_AT or CHECK_NOW must be set.")
    sys.exit(-1)

def check():
    ''' Do the actual processing and check all libraries for incorrect matches '''
    plex = PlexServer(PLEX_URL, PLEX_TOKEN)

    for section in plex.library.sections():
        if not "*" in CHECK_LIBRARY and not section.title.lower() in CHECK_LIBRARY:
            continue

        count = 0
        folders = []
        oldLabels = []

        logger.info(f'{section.title}: Processing')

        availableFilters = [f.filter for f in section.listFilters()]
        if "label" in availableFilters:
            availableChoices = [f.title for f in section.listFilterChoices("label")]
            if LABEL in availableChoices:
                oldLabels = [m.guid for m in section.search(filters = {"label": LABEL})]

        # This is generally very quick for 10k+ folders
        for path in section.locations:
            try:
                if not path.endswith("/"):
                    path = path + "/"
                for fix in CHECK_PATHS:
                    path = path.replace(fix, CHECK_PATHS[fix])
                if os.path.isdir(path):
                    folders = folders + glob(path + "*")
                else:
                    logger.error(f'{section.title}: Not a directory, "{path}"')
            except:
                logger.error(f'{section.title}: Error listing files at "{path}"')
                raise

        if not len(folders):
            logger.debug(f'{section.title}: No content found, skipping')
            continue

        # Say if this might take a long time
        logger.debug(f'{section.title}: Loading library {len(folders)} folders{", please be patient" if len(folders) > 5000 else ""}')

        updates = []
        items = section.all() # This may take a long time
        index = 1
        total = len(items)

        logger.debug(f'{section.title}: Library loaded, cross-referencing folders')

        for item in items:
            if isTTY:
                logger.debug(f'  [{index}/{total}]\033[F')
            index += 1
            found = False
            correct = False
            for guid in item.guids:
                if any([guid.id.startswith(f'{agent}:') for agent in CHECK_AGENTS]):
                    found = True
                    id = f'{{{guid.id[:4]}-{guid.id[7:]}}}' # "{<agent>-<id>}"
                    if any([id in folder for folder in folders]):
                        correct = True
                        break # Don't need to check for other agents

            if found and correct:
                if item.guid in oldLabels:
                    item.removeLabel(LABEL)
            else:
                count += 1
                updates.append(item)
                logger.warning(f'  {"Unmatched" if not found else "Incorrect"}: {item.title} ({item.year})')
                if CHECK_ADD_LABEL:
                    item.addLabel(LABEL)
                if CHECK_UNMATCH:
                    item.unmatch()

        logger.debug(f'{section.title}: Done, {count if count else "nothing"} found.{f' Filter label="{LABEL}" in Plex' if count and CHECK_ADD_LABEL else ""}')

try:
    if CHECK_NOW:
        check()
    else:
        logger.info(f'Checking at {", ".join(CHECK_AT)} every day...')
        for checkTime in CHECK_AT:
            schedule.every().day.at(checkTime).do(check)
        while True:
            schedule.run_pending()
            sleep(10)
except KeyboardInterrupt:
    sys.exit(0)
