#!/bin/sh
# Prepare data unless a release job already did so, then run the server command.
set -eu
cd /home/app/web
# Multi-replica deployments should run prepare.sh once as a release job.
if [ "${PREPARE_ON_START:-1}" = "1" ]; then
    sh ./prepare.sh
fi
exec "$@"
