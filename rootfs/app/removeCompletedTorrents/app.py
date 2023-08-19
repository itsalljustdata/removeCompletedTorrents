#!/bin/python
from pathlib import Path
# from os.path import islink
# from os import getenv
from stat import *

from config import logger, getConfig

from qbittorrentapi import Client
import datetime
import time
# from pyarr import SonarrAPI, RadarrAPI
# import json

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
    
    # if DEBUG:
    #     logger.info (clientParams)
        
    # >>> client = Client(host='localhost:8080', username='admin', password='adminadmin')
    # >>> torrents = client.torrents_info()
    qbt_client = Client (**clientParams)
    
    # if DEBUG:
    #     ic(qbt_client.__dict__)

    # if DEBUG:
    #     logger.info ("Getting Completed")
    completed = qbt_client.torrents_info(status_filter='completed')
    # if DEBUG:
    #     logger.info (f"{len(completed)} : Got Completed")

    # if DEBUG:
    #     logger.info ("Filtering")
    torrents = [t for t in completed if 'category' in t and t['category']]
    # if DEBUG:
    #     logger.info (f"{len(torrents)} : Filtered")

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
            # if DEBUG and ix==1:
            #     t.pop('magnet_uri',False)
            #     logger.info ('-'*80)
            #     logger.info (t)
            #     logger.info ('-'*80)

        # # Instantiate SonarrAPI Object
        # sonarr = SonarrAPI(host_url = "http://localhost:8989", api_key = "7c6348455e9545c29ec3ac091b5b726a",ver_uri = '')
        # radarr = RadarrAPI(host_url = "http://localhost:7878", api_key = "ff30391cb5314cbe9fc8ce19d21ee84d")

        # absBasePath = Path(__file__).parent
        
        # # try:
        # # except:
        # #     profiles = []

        # noHardlinks.append('Conversation, The (1974)')
        # for ix_h, h in enumerate([h for h in noHardlinks]):

        #     basePath = absBasePath.joinpath(str(ix_h))
        #     print ('-'*80)
        #     logger.info (ix_h, h)

        #     def doParse (theTitle, thisAPI, thisAPIName):
        #         try:
        #             apiResp = thisAPI.get_parsed_title(title = h)
        #         except AttributeError:
        #             apiResp = thisAPI.assert_return("parse", thisAPI.ver_uri, list, {"title": h})
        #         ok = False
        #         profiles = []
        #         if isinstance(apiResp,list
        #     S
        # '{thisAPIName}.profiles.json').write_text(json.dumps(profiles,indent=2))
        # #             ok = True
        #             print (f"{thisAPIName} Match")
        #         except KeyError:
        #             print (f"No {thisAPIName} Match")
        #         return [ok, apiResp, profiles]
        #     def workItOut (theTitle):
        #         theAPI   = None
        #         apiResp  = {}
        #         profiles = []
                
        #         for api in [[sonarr,'sonarr'], [radarr,'radarr']]:
        #             ok, apiResp, profiles = doParse(theTitle, api[0], api[1])
        #             if ok:
        #                 return [api[0], apiResp, profiles, api[1]]
        #         return [None, apiResp, profiles,None]

        #     theAPI, apiResp, profiles, apiName = workItOut(h)
        #     logger.info (h, apiName)

        #     if isinstance(apiResp,list):
        #         apiResp = apiResp[0]
        #     # try:
        #     #     logger.info (apiResp["series"]["id"])
        #     # except KeyError:
        #     #     logger.info ("No Sonarr Match")
        #     basePath.with_suffix('.parse.json').write_text(json.dumps(apiResp,indent=2))
        #     try:
        #         thisQuality = apiResp["parsedEpisodeInfo"]["quality"]["quality"]["id"]
        #     except KeyError:
        #         thisQuality = 0
        #     logger.info (thisQuality)

        #     try:
        #         seriesQualProfile = [d for d in profiles if d["id"] == apiResp["series"]["qualityProfileId"]][0]["items"]
        #         seriesQualProfile = {ix : d["quality"] for ix,d in enumerate(seriesQualProfile) if d["allowed"] == True}
        #     except:
        #         seriesQualProfile = None

        #     def findQualIndex (qualId):
        #         if (not qualId or qualId == 0):
        #             ...
        #         else:
        #             for f in seriesQualProfile.keys():
        #                 if seriesQualProfile[f]["id"] == qualId:
        #                     CONFIG
        #     thisQualIndex = findQualIndex(thisQuality)
        #     logger.info (thisQualIndex)

        #     # logger.info (h)
        #     def dumpKeys(theDict, theIndent, prefix = None):
        #         indentIncrement = 4
        #         nextIndent = theIndent+indentIncrement
        #         lineStart = f"{' '*theIndent}{type(theDict).__name__.upper()}"
        #         if isinstance(theDict,dict):
        #             for k in theDict:
        #                 lineStart = ' '*theIndent
        #                 if prefix:
        #                     lineStart += f"{prefix}. "
        #                 lineStart+= k
        #                 print (f"{lineStart} : {type(theDict[k]).__name__}")
        #                 if isinstance(theDict[k],dict) or isinstance(theDict[k],list):
        #                     dumpKeys(theDict[k],nextIndent,prefix)
        #         else:
        #             if theIndent == 0:
        #                 print (lineStart)
                    
        #             if isinstance(theDict,list):
        #                 for ix,d in enumerate(theDict):
        #                     dumpKeys (d, nextIndent, ix)

        #     fileId = []
        #     thisResolution = None
        #     try:
        #         epExists = False
        #         eps = apiResp["episodes"]
        #         for e in eps:
        #             fileId.append(e["episodeFileId"])
        #             if fileId:
        #                 epExCONFIG
        #     except KeyError as ke:
        #         epExists = False

        #     if fileId:
        #         for ix_f,f in enumerate(fileId):
        #             apiResp = sonarr.get_episode_file(id_ = f)
        #             # apiResp = callAPISingleParam("episodefile","episodeFileIds",f)
        #             def doThisFile (theDict,the_ix = None):
        #                 basePath.with_suffix(f'.{ix_f}.{the_ix}.fileGet.json').write_text(json.dumps(theDict,indent=2))
        #                 try:
        #                     existingQuality = theDict["quality"]["quality"]["id"]
        #                 except KeyError:
        #                     existingQuality = 0
        #                 # logger.info (existingQuality,thisQuality,seriesQualProfile)

        #                 existingQualIndex = findQualIndex(existingQuality)
        #                 logger.info (existingQualIndex, thisQualIndex)
        #                 if existingQualIndex and thisQualIndex and existingQualIndex > thisQualIndex:
        #                     # We've already got a better version
        #                     string = f"Deleting. This is \"{seriesQualProfile[thisQualIndex]['name']}\", already got \"{seriesQualProfile[existingQualIndex]['name']}\""
        #                     print(string)

        #             if isinstance (apiResp,list):
        #                 for ix_q, q in enumerate(apiResp):
        #                     doThisFile(q,ix_q)
        #             else:
        #                 doThisFile (apiResp)
                        
        #         # dumpKeys(apiResp,0)


        joinStr = ',\n'
        logger.info (f'Hard Links    : {len(hardlinks)}')
        logger.info (f'No Hard Links : {len(noHardlinks)}')
        if len(hardlinks) > 0:
            logger.debug (f"Hard Links    -\n {joinStr.join(hardlinks)}")
        if len(noHardlinks) > 0:
            
            if len(noHardlinks) <= 10:
                logger.debug (f"No Hard Links -\n {joinStr.join(noHardlinks)}")
            else:
                logger.debug (f"No Hard Links - {len(noHardlinks)}")

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
    # logger.info ('runFromCmd')
    CONFIG = getConfig()
    # logger.info (str(CONFIG))
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