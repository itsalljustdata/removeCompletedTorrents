#!/usr/bin/bash

PUID=${PUID:-1000}

if [ "`pgrep --uid ${PUID} -f removeCompletedTorrents`" == "" ]; then
    echo "removeCompletedTorrents - Not running"
    exit 1
fi
exit 0