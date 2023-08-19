#!/bin/python
from configFileHelper import Config
from pathlib import Path
# from datetime import datetime
import collections.abc
import logging
from sys import stdout
from copy import deepcopy
from os import getenv

# CRITICAL = logging.CRITICAL
# FATAL    = logging.FATAL
# ERROR    = logging.ERROR
# WARNING  = logging.WARNING
# WARN     = logging.WARN
# INFO     = logging.INFO
# DEBUG    = logging.DEBUG
# NOTSET   = logging.NOTSET

# DEFAULT_LOG_LEVEL = INFO


if not (thisLoggerName := getenv('HOST_CONTAINERNAME')):
    thisLoggerName = 'removeCompletedTorrents'
logger = logging.getLogger(thisLoggerName)
logFormat = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
formatter = logging.Formatter(logFormat)
logger.setLevel(logging.INFO)

def setAndAddLogger (theHandler, theFormatter : logging.Formatter = formatter):
    theHandler.setFormatter(deepcopy(theFormatter))
    logger.addHandler(theHandler)

def addHandler (theHandler):
    qq = [h for h in logger.handlers if type(h) == type(theHandler)]
    for q in qq:
        logger.removeHandler(q)
    logger.addHandler(theHandler)

setAndAddLogger (logging.StreamHandler(stdout))


def update(d, u):
    for k, v in u.items():
        if isinstance(v, collections.abc.Mapping):
            d[k] = update(d.get(k, {}), v)
        else:
            d[k] = v
    return d

def checkLogLevel (theLoglevel: str):
    if not theLoglevel:
        theLoglevel = logging.INFO
    elif theLoglevel == "WARN":
        theLoglevel = "WARNING"
    try:
        theLoglevelInt = abs(int(theLoglevel))
        loglevelName   = logging.getLevelName(theLoglevelInt)
    except ValueError as e:
        if theLoglevel.upper() not in logging._nameToLevel:
            logger.critical ((msg := f"Invalid Log Level : {theLoglevel}"))
            raise Exception (msg)
        loglevelName = theLoglevel
    # logger.critical (f"{theLoglevel} - {loglevelName}")
    return loglevelName

def getConfig():

    config        = Config(file_path = Path("config.default.yml").resolve())
    theConfigFile = Path("config.yml").resolve()
    
    if theConfigFile.exists():
        config.params = update(config.params,Config(file_path=theConfigFile).params)
    else:
        logger.warning (f'Using defaults only - {theConfigFile} does not exist' )
        
    ll = ['APP','LOG_LEVEL']
    logger.setLevel((logLevel := checkLogLevel(config.get(keys=ll,raiseNDF=False))))
    config.set(ll, logLevel)
            
    logger.info (config.get('APP'))

    # Just make sure the host is set!
    _ = config.get(['QBIT','host'])
    
    try:
        config.save_as (theConfigFile)
    except OSError as oe:
        if oe.errno == 30: # Read only FS
            logger.critical(f"{oe.filename} : Cannot write : {oe.args[1]}")
        else:
            raise oe

    return config