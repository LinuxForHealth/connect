#!/usr/bin/env sh
# uninstall-certificates.sh
# removes the LinuxForHealth CA and other trusted certificates from the local trust store and file system
SCRIPT_DIRECTORY=$(dirname "$0")

mkcert -uninstall
rm "$SCRIPT_DIRECTORY"/*.pem "$SCRIPT_DIRECTORY"/*.key
