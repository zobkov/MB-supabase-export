#!/bin/bash
set -e

systemctl restart mb-helper-bot.service
journalctl -u mb-helper-bot.service -f
