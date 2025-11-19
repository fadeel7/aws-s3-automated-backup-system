# AWS S3 Automated Backup System

A serverless, event-driven backup solution that automatically replicates files across AWS regions for disaster recovery and data redundancy.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [AWS Services Used](#aws-services-used)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Testing](#testing)
- [Monitoring](#monitoring)
- [Cost Estimation](#cost-estimation)
- [Troubleshooting](#troubleshooting)
- [Future Enhancements](#future-enhancements)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project implements an automated backup system using AWS serverless technologies. When a file is uploaded to the source S3 bucket, an event notification triggers a Lambda function that copies the file to a backup bucket in a different AWS region and sends a notification via email.

### Key Benefits
- **Zero server management**: Fully serverless architecture
- **Automatic disaster recovery**: Cross-region replication protects against regional failures
- **Real-time notifications**: Instant email alerts for backup operations
- **Cost-effective**: Pay-per-use pricing model with minimal costs
- **Scalable**: Handles varying workloads without manual intervention

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Action                              │
│                    Upload File to S3                             │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   S3 Source Bucket (us-east-1)                   │
│                  Generates Event Notification                    │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AWS Lambda Function                           │
│              - Receives S3 event notification                    │
│              - Copies file to backup bucket                      │
│              - Publishes to SNS topic                            │
│              - Logs to CloudWatch                                │
└──────────┬────────────────────────────┬─────────────────────────┘
           │                            │
           ▼                            ▼
┌──────────────────────┐    ┌──────────────────────────────────┐
│  S3 Backup Bucket    │    │     Amazon SNS Topic             │
│   (us-west-2)        │    │  Sends Email Notification        │
│ Cross-region replica │    └──────────────────────────────────┘
└──────────────────────┘
```

### Data Flow
1. User uploads file to source S3 bucket in US East (Virginia)
2. S3 event notification triggers Lambda function
3. Lambda function extracts file metadata from event
4. Lambda copies file to backup bucket in US West (Oregon)
5. Lambda publishes success/failure message to SNS topic
6. SNS delivers email notification to subscribers
7. All operations logged to CloudWatch for monitoring

## Features

- **Automated Cross-Region Backup**: Files automatically replicated from us-east-1 to us-west-2
- **Event-Driven Architecture**: Backup triggered immediately upon file upload
- **Email Notifications**: Receive instant alerts for successful and failed backups
- **Comprehensive Logging**: All operations logged to CloudWatch for audit and debugging
- **Error Handling**: Robust error handling with detailed failure notifications
- **Secure**: IAM roles with least-privilege permissions
- **Versioning**: S3 versioning enabled for protection against accidental overwrites

## AWS Services Used

| Service | Purpose |
|---------|---------|
| Amazon S3 | Object storage for source and backup buckets |
| AWS Lambda | Serverless compute for backup logic execution |
| Amazon SNS | Notification service for email alerts |
| AWS IAM | Identity and access management for permissions |
| Amazon CloudWatch | Monitoring and logging service |

## Prerequisites

- AWS Account with appropriate permissions
- Basic understanding of AWS Console
- Email address for notifications
- AWS CLI (optional, for advanced configuration)

## Installation

### Step 1: Create S3 Buckets

**Source Bucket (us-east-1):**
```bash
# Via AWS Console:
# 1. Navigate to S3 service
# 2. Create bucket: source-backup-[your-name]-2024
# 3. Region: US East (N. Virginia)
# 4. Enable versioning
# 5. Enable encryption (SSE-S3)
# 6. Block all public access
```

**Backup Bucket (us-west-2):**
```bash
# Via AWS Console:
# 1. Navigate to S3 service
# 2. Create bucket: backup-bucket-[your-name]-2024
# 3. Region: US West (Oregon)
# 4. Enable versioning
# 5. Enable encryption (SSE-S3)
# 6. Block all public access
```

### Step 2: Create SNS Topic and Subscription

```bash
# Via AWS Console:
# 1. Navigate to SNS service
# 2. Create topic: BackupNotificationTopic
# 3. Type: Standard
# 4. Create email subscription with your email address
# 5. Confirm subscription via email
# 6. Note the Topic ARN for later use
```

### Step 3: Create IAM Role for Lambda

```bash
# Via AWS Console:
# 1. Navigate to IAM > Roles
# 2. Create role for Lambda service
# 3. Attach policies:
#    - AWSLambdaBasicExecutionRole
#    - AmazonS3FullAccess
#    - AmazonSNSFullAccess
# 4. Name: S3BackupLambdaRole
```

### Step 4: Create Lambda Function

```bash
# Via AWS Console:
# 1. Navigate to Lambda service
# 2. Create function: S3AutoBackupFunction
# 3. Runtime: Python 3.12
# 4. Execution role: Use existing role (S3BackupLambdaRole)
# 5. Upload lambda_function.py from this repository
# 6. Configure environment variables (see Configuration section)
# 7. Increase timeout to 30 seconds
```

### Step 5: Configure S3 Event Notification

```bash
# Via AWS Console:
# 1. Navigate to source S3 bucket
# 2. Properties > Event notifications
# 3. Create event notification
# 4. Event types: All object create events
# 5. Destination: Lambda function (S3AutoBackupFunction)
```

## Configuration

### Lambda Environment Variables

Configure the following environment variables in your Lambda function:

| Variable | Description | Example |
|----------|-------------|---------|
| BACKUP_BUCKET | Name of backup S3 bucket | backup-bucket-john-2024 |
| SNS_TOPIC_ARN | ARN of SNS topic | arn:aws:sns:us-east-1:123456789012:BackupNotificationTopic |

### Lambda Function Settings

- **Timeout**: 30 seconds
- **Memory**: 128 MB
- **Runtime**: Python 3.12
- **Architecture**: x86_64

## Usage

### Basic Usage

1. Navigate to your source S3 bucket in AWS Console
2. Click "Upload" and select file(s)
3. Click "Upload" to initiate transfer
4. Lambda function automatically triggers
5. Check backup bucket in us-west-2 region for replicated file
6. Check email for backup notification

### Monitoring Backups

**Via CloudWatch Logs:**
```bash
# Navigate to CloudWatch > Log groups
# Open: /aws/lambda/S3AutoBackupFunction
# View latest log stream for execution details
```

**Via Email Notifications:**
- Success notifications include file name, size, and timestamp
- Failure notifications include error details and troubleshooting guidance

## Testing

### Manual Test

1. Create a test file (e.g., test.txt)
2. Upload to source bucket
3. Verify file appears in backup bucket within 5-10 seconds
4. Check email for notification
5. Review CloudWatch logs for execution details

### Lambda Test Event

Use this test event to manually trigger Lambda:

```json
{
  "Records": [
    {
      "s3": {
        "bucket": {
          "name": "your-source-bucket-name"
        },
        "object": {
          "key": "test-file.txt",
          "size": 1024
        }
      }
    }
  ]
}
```

## Monitoring

### CloudWatch Metrics

Monitor these key metrics:
- **Invocations**: Total number of Lambda executions
- **Duration**: Execution time per invocation
- **Errors**: Failed executions
- **Throttles**: Rate-limited executions

### CloudWatch Alarms (Recommended)

Set up alarms for:
- Error rate exceeding threshold
- Duration exceeding expected values
- Failed backup operations

### Log Analysis

Key log entries to monitor:
- "LAMBDA FUNCTION STARTED" - Execution initiated
- "Copy operation successful" - File copied successfully
- "SNS notification sent" - Email notification delivered
- Error messages - Detailed failure information

## Cost Estimation

### AWS Free Tier (First 12 Months)
- S3: 5GB storage
- Lambda: 1 million requests, 400,000 GB-seconds compute
- SNS: 1,000 email notifications
- CloudWatch: 5GB logs

### Beyond Free Tier (Approximate Monthly Costs)
Assuming 1,000 file backups per month, 10MB average file size:

| Service | Usage | Cost |
|---------|-------|------|
| S3 Storage | 10GB | $0.23 |
| Lambda Requests | 1,000 | $0.0002 |
| Lambda Compute | 1,000 x 1s x 128MB | $0.002 |
| SNS Notifications | 1,000 emails | $0.50 |
| CloudWatch Logs | 1GB | $0.50 |
| **Total** | | **~$1.25/month** |

## Troubleshooting

### Issue: Lambda Not Triggering

**Symptoms**: No CloudWatch logs, no backups created

**Solutions**:
- Verify S3 event notification is configured
- Check Lambda trigger appears in Lambda console
- Ensure IAM role allows S3 to invoke Lambda
- Confirm event type includes object creation

### Issue: Permission Denied Errors

**Symptoms**: Errors in CloudWatch logs mentioning "Access Denied"

**Solutions**:
- Verify IAM role attached to Lambda
- Confirm role contains S3 and SNS policies
- Check bucket policies don't explicitly deny access
- Ensure backup bucket exists in correct region

### Issue: No Email Notifications

**Symptoms**: Backups work but no emails received

**Solutions**:
- Confirm SNS subscription status is "Confirmed"
- Check spam/junk folder
- Verify SNS_TOPIC_ARN environment variable is correct
- Test SNS topic independently by publishing test message

### Issue: Files Not Appearing in Backup Bucket

**Symptoms**: Lambda executes but files missing from backup

**Solutions**:
- Verify you're viewing correct region (us-west-2)
- Check BACKUP_BUCKET environment variable matches exact bucket name
- Review CloudWatch logs for copy operation errors
- Confirm backup bucket exists and is accessible

## Future Enhancements

### Planned Features
- [ ] Support for selective backup based on file type or size
- [ ] Integration with DynamoDB for backup metadata tracking
- [ ] Automated lifecycle policies for backup retention
- [ ] Support for backup to multiple regions simultaneously
- [ ] File integrity verification using checksums
- [ ] Web dashboard for backup monitoring
- [ ] Slack/Teams integration for notifications
- [ ] Cost optimization with S3 Intelligent-Tiering

### Scalability Improvements
- [ ] Multi-part upload for files larger than 5GB
- [ ] Batch processing for multiple concurrent uploads
- [ ] Dead letter queue for failed backup operations
- [ ] Circuit breaker pattern for external service calls

### Security Enhancements
- [ ] KMS encryption for S3 buckets
- [ ] VPC endpoints for private communication
- [ ] Least-privilege IAM policies with specific resource ARNs
- [ ] AWS Secrets Manager for sensitive configuration

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

Please ensure:
- Code follows Python PEP 8 style guidelines
- All functions include docstrings
- Error handling is comprehensive
- CloudWatch logging is detailed

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- AWS Documentation for serverless best practices
- Cloud computing community for architectural patterns
- Open source contributors for inspiration

## Contact

Fadeel Darkwa

Project Link: [https://github.com/fadeel7/aws-s3-backup-system](https://github.com/fadeel7/aws-s3-backup-system)

---

**Note**: This project is designed for educational purposes and demonstrates AWS serverless architecture concepts. For production use, implement additional security hardening, monitoring, and compliance measures appropriate for your organization.