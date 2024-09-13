#!/bin/sh

# Copy Django generated static files to shared files
# NGINX will serve these files as it also mounts the shared files volume
cp -r /usr/src/app/static /shared-files/
