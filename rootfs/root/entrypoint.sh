#!/bin/bash

# set -e

runUser=${__RUN_USER:-iajd}
runGroup=${__RUN_GROUP:-iajd}

PUID=${PUID:-1000}
PGID=${PGID:-1000}

uid=`id -u ${runUser}`
gid=`id -g ${runGroup}`

change=0

# Set GroupId
if [ ${gid} -ne ${PGID} ]; then
    echo "${runGroup} : existing GID (${gid}) is different to PGID (${PGID})"
    tmp=`grep ":${PGID}:" /etc/group | cut -d: -f 1`
    if [ "$tmp" == "" ]; then
        echo "${runGroup} : Changing GID from ${gid} to ${PGID}"
        groupmod --gid $PGID ${runGroup}
    else
        runGroup=$tmp
        echo "GID ${PGID} already exists: running as group \"${runGroup}\""
    fi
    change=1
fi

# Set UserId
if [ ${uid} -ne ${PUID} ]; then
    echo "${runUser} : existing UID (${uid}) is different to PUID (${PUID})"
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
    fi
    change=1
fi

if [ $change -ne 0 ]; then
   usermod -aG ${PGID} --gid ${PGID} ${runUser}
   chown -R ${PUID}:${PGID} /app
fi

echo "Spawning removeCompletedTorrents as user \"${runUser}\", group \"${runGroup}\""

su --group ${runGroup} --command 'bash /app/run.sh' ${runUser}