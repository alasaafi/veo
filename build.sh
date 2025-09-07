#!/usr/bin/env bash
# exit on error
set -o errexit

# Use sudo for admin privileges
sudo apt-get update 
sudo apt-get install -y ffmpeg