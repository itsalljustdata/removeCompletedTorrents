#!/bin/sh

if [ "`pgrep -f removeCompletedTorrents.py`" == "" ]; then
    echo "removeCompletedTorrents.py - Not running"
    exit 1
fi
exit 0