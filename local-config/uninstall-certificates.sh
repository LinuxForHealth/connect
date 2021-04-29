#!/usr/bin/env sh
# uninstall-certificates.sh
# removes the LinuxForHealth CA and other trusted certificates from the local trust store and file system
OUTPUT_DIRECTORY=$(dirname "$0")/certs

mkcert -uninstall
rm "$OUTPUT_DIRECTORY"/*.pem "$OUTPUT_DIRECTORY"/*.key
