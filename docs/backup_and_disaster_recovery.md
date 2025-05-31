# Backup and Disaster Recovery

## Automated Firestore Backups
- Scheduled via Cloud Scheduler daily at 2am UTC.
- Exports all Firestore documents to a dedicated GCS bucket.
- Terraform (`infra/terraform/firestore_backup.tf`) automates bucket and scheduler setup.

## Critical Config Backup
- `infra/scripts/backup_config.sh` backs up all JSON config files to a GCS bucket.
- Add to CI/CD or cron for regular execution.

## Recovery Validation (Runbook)
1. **Firestore Restore**
    - Use GCP Console or `gcloud`:
      ```
      gcloud firestore import gs://<backup-bucket>/exports/<timestamp>/
      ```
    - Validate data and app functionality post-restore.
2. **Config Restore**
    - Retrieve latest config backup from GCS:
      ```
      gsutil cp gs://<backup-bucket>/config/<date>/*.json config/
      ```
    - Restart affected services.
3. **Test Recovery**
    - Schedule periodic restore tests in a staging environment.
    - Document results and update runbook as needed.

## High Availability Notes
- Backups are stored in multi-region GCS for durability.
- Regular recovery drills ensure integrity and readiness.
