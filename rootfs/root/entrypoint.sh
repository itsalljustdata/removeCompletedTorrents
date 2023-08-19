#!/bin/bash

set -e

runUser=${__RUN_USER:-iajd}
runGroup=${__RUN_GROUP:-iajd}

PUID=${PUID:-1000}
PGID=${PGID:-1000}

uid=`id -u ${runUser}`
gid=`id -g ${runGroup}`

# Set GroupId
if [ ${gid} -ne ${PGID} ]; then
    tmp=`grep ":${PGID}:" /etc/group | cut -d: -f 1`
    if [ "$tmp" == "" ]; then
        echo "${runGroup} : Changing GID from ${gid} to ${PGID}"
        groupmod --gid $PGID ${runGroup}
    else
        runGroup=$tmp
        echo "GID ${PGID} already exists: running as group \"${runGroup}\""
        usermod -aG $PGID ${runUser}
    fi
fi

# Set UserId
if [ ${uid} -ne ${PUID} ]; then
    tmp=`id -nu $PUID 2> /dev/null`
    if [ "${tmp}" == "" ]; then
        echo "${runUser} : Changing UID from ${uid} to ${PUID}"
        usermod --uid ${PUID} ${runUser}
    else
        runUser=$tmp
        echo "UID ${PUID} already exists: running as \"${runUser}\""

        status=`passwd -S ${runUser} | cut -d' ' -f 2 2> /dev/null`
        if [ "${status:0:1}" == "L" ]; then
            echo "Account \"${runUser}\" is locked. Cannot proceed. Modify PUID environment variable"
            exit 1
        fi
        
        passwdEntry=`grep "^${runUser}:" /etc/passwd`
        mkdir -p `echo $passwdEntry | cut -d: -f 6` 2> /dev/null
        usermod -aG $PGID ${runUser}
    fi
fi

chown -R ${runUser}:${runGroup} /app

echo "Spawning removeCompletedTorrents as user \"${runUser}\", group \"${runGroup}\""

su --group ${runGroup} --command 'bash /app/run.sh' ${runUser}