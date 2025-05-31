# Monitoring Dashboards and Alerts

This folder contains Terraform configurations for Google Cloud Monitoring dashboards and alert policies for the AI Handyman Secretary Assistant project.

## Dashboards
- **System Health Overview:** Visualizes request latency, Firestore document reads, GKE CPU usage, and application error rates.
- **Cost Optimization:** Shows estimated monthly billing.

## Alerts
- **High Application Error Rate:** Triggers when error rate exceeds 2% for 5 minutes.
- **High Request Latency:** Triggers if average request latency exceeds 1000ms for 5 minutes.
- **High Estimated Billing Cost:** Alerts if projected costs exceed $500.

## Setup
1. Configure your `terraform.tfvars` with `project_id`, `region`, and `notification_channel_id`.
2. Run `terraform init && terraform apply` in the `monitoring/terraform/` directory.

## Customization
- Add more widgets or alerts as needed for services like Twilio, Stripe, etc., by editing `main.tf`.
