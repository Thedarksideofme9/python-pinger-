#!/bin/bash

# Check if a hostname is provided
if [ $# -ne 1 ]; then
  echo "Usage: ./simple_ping.sh <hostname>"
  exit 1
fi

hostname="$1"

# Determine OS and use appropriate command. It checks for Windows Subsystem for Linux because it needs the windows pinger to work
if [[ "$OSTYPE" == "msys" ]]; then
    ping -n 1 "$hostname" > /dev/null
else
    ping -c 1 "$hostname" > /dev/null
fi

if [ $? -eq 0 ]; then
  echo "Ping to $hostname successful."
else
  echo "Ping to $hostname failed."
  exit 1
fi
