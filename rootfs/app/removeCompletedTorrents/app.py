#!/bin/python
from pathlib import Path
from stat import *

from config import logger, getConfig

from qbittorrentapi import Client
import datetime
import time

DEBUG : bool = False

def datetime_to_local_timezone(dt):
    epoch = dt.timestamp() # Get POSIX timestamp of the specified datetime.
    st_time = time.localtime(epoch) #  Get struct_time for the timestamp. This will be created using the system's locale and it's time zone information.
    tz = datetime.timezone(datetime.timedelta(seconds = st_time.tm_gmtoff)) # Create a timezone object with the computed offset in the struct_time.

    return dt.astimezone(tz) # Move the datetime instance to the new time zone.

def removeCompleted(clientParams: dict, arr_cleanup_delay_s : int):
    logger.debug (clientParams)
    if arr_cleanup_delay_s > 0:
        timestampCutoff = int(datetime.datetime.timestamp(datetime_to_local_timezone(datetime.datetime.utcnow()))) - arr_cleanup_delay_s
    elif arr_cleanup_delay_s < 0:
        timestampCutoff = None
    else:
        timestampCutoff = 0

    def stat_to_dict(s_obj) -> dict:
        return {k[3:]: getattr(s_obj, k) for k in dir(s_obj) if k.startswith('st_')}

    sanity = 0
    while True:
        try:
            sanity+=1
            qbt_client = Client (**clientParams)
            break
        except Exception as e:
            if sanity > 10:
                raise e
            time.sleep(30)
            
    completed = qbt_client.torrents_info(status_filter='completed')
    
    torrents = [t for t in completed if 'category' in t and t['category']]
    
    if len(torrents) == 0:
        logger.debug ("No completed torrents found")
    else:
        logger.debug (f"{len(torrents)} completed torrents found")

        noHardlinks = []
        hardlinks = []
        
        padLen = len(str(len(torrents)))

        for ix, t in enumerate(torrents):
            q = f"{str(ix+1).rjust(padLen)}. {t['name']}"
            logger.debug (q)
            q = None
            savePath = Path(t['save_path'])
            t['canDelete'] = 0

            t['files'] = qbt_client.torrents_files(torrent_hash = t.hash)

            if t['category'][-3:] == 'arr' and timestampCutoff and t['completion_on'] < timestampCutoff:
                logger.info(f"Old enough to be deleted : {t['name']}")
                t['canDelete'] = 1
            else:
                for f in t['files']:
                    f['fullPath']   = savePath.joinpath(f["name"])
                    f['exists']     = f['fullPath'].is_file()
                    if f['exists']:
                        s = f['fullPath'].stat()
                        f['hardlinked'] = s.st_nlink
                        f['stat']       = stat_to_dict(s)
                        if f['hardlinked'] > 1:
                            t['canDelete'] += 1
                    else:
                        f['hardlinked'] = None
                    
            if t['canDelete'] == 0:
                logger.debug ("Not hardlinked")
                noHardlinks.append(t['name'])
            else:
                logger.debug ("Hardlinked")
                hardlinks.append(t['name'])
        joinStr = ',\n'
        
        if len(hardlinks) > 0:
            logger.info (f"Hard Links    -\n {joinStr.join(hardlinks)}")
        if len(noHardlinks) > 0:
            
            if len(noHardlinks) <= 10:
                logger.debug (f"No Hard Links -\n {joinStr.join(noHardlinks)}")
            else:
                logger.indo (f"No Hard Links - {len(noHardlinks)}")

        if len(hardlinks) > 0:
            deletes =   [{"delete_files" : True, "torrent_hashes" : [t["hash"] for t in torrents if t['canDelete'] > 0]}
                        # ,{"torrent_hashes" : [t["hash"] for t in torrents if t['canDelete'] == 0]}
                        ]
            logger.debug (deletes)
            for d in deletes:
                qbt_client.torrents_delete(**d)
    logger.debug ("Logout : Before")
    qbt_client.auth_log_out()
    logger.debug ("Logout : After")

def sleepy (sleepy_time_s : int):
    logger.debug (f'Napping for {sleepy_time_s}s')
    time.sleep(sleepy_time_s)
 
def runFromCmd():
    CONFIG = getConfig()
    appConfig  = CONFIG.get('APP')
    qbitConfig = CONFIG.get('QBIT')
    
    global DEBUG
    DEBUG = appConfig.get('DEBUG',False)
    import time
    sleepy_time = appConfig.get('SLEEPY_TIME',1800)
        
    arr_cleanup_delay_s =  int(appConfig.get('ARR_CLEANUP_DELAY_S',None))
    
    while True:
        removeCompleted(clientParams = qbitConfig, arr_cleanup_delay_s = arr_cleanup_delay_s)
        sleepy(sleepy_time_s = sleepy_time)

def run():
    logger.info ('Startup')
    runFromCmd()

if __name__ == "__main__":
    run()
