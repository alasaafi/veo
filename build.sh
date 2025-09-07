#!/usr/bin/env bash
# exit on error
set -o errexit

# Installer ffmpeg
apt-get update && apt-get install -y ffmpeg