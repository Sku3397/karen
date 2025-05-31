#!/bin/bash
# Backup critical config files to GCS
gsutil cp config/*.json gs://$CONFIG_BACKUP_BUCKET/config/$(date +%F)/
