"""
AWS S3 Automated Backup System - Lambda Function

This Lambda function automatically copies files from a source S3 bucket
to a backup bucket in a different AWS region when triggered by S3 events.
It sends email notifications via SNS for all backup operations.

"""

import json
import boto3
import os
from datetime import datetime
from typing import Dict, Any

# Initialize AWS service clients
s3_client = boto3.client('s3')
sns_client = boto3.client('sns')

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler function triggered by S3 events.
    
    This function processes S3 object creation events, copies files to a backup
    bucket, and sends notifications about the operation status.
    
    Args:
        event (dict): S3 event notification containing file upload details
        context (object): Lambda context object with runtime information
        
    Returns:
        dict: Response object with statusCode and body
        
    Raises:
        Exception: Re-raises any exceptions after logging and notification
    """
    
    print("=" * 60)
    print("BACKUP OPERATION STARTED")
    print("=" * 60)
    
    # Log the complete event for debugging
    print(f"Event received: {json.dumps(event, indent=2)}")
    
    try:
        # Retrieve environment variables
        backup_bucket = os.environ.get('BACKUP_BUCKET')
        sns_topic_arn = os.environ.get('SNS_TOPIC_ARN')
        
        # Validate environment variables
        if not backup_bucket:
            raise ValueError("BACKUP_BUCKET environment variable not set")
        if not sns_topic_arn:
            raise ValueError("SNS_TOPIC_ARN environment variable not set")
        
        print(f"Configuration:")
        print(f"  Backup Bucket: {backup_bucket}")
        print(f"  SNS Topic: {sns_topic_arn}")
        
        # Extract file information from S3 event
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        object_key = event['Records'][0]['s3']['object']['key']
        file_size = event['Records'][0]['s3']['object']['size']
        event_time = event['Records'][0]['eventTime']
        
        print(f"\nFile Details:")
        print(f"  Source Bucket: {source_bucket}")
        print(f"  Object Key: {object_key}")
        print(f"  Size: {file_size} bytes ({file_size / 1024:.2f} KB)")
        print(f"  Event Time: {event_time}")
        
        # Perform the copy operation
        print(f"\nInitiating copy operation...")
        print(f"  FROM: s3://{source_bucket}/{object_key}")
        print(f"  TO:   s3://{backup_bucket}/{object_key}")
        
        copy_source = {
            'Bucket': source_bucket,
            'Key': object_key
        }
        
        copy_response = s3_client.copy_object(
            CopySource=copy_source,
            Bucket=backup_bucket,
            Key=object_key,
            ServerSideEncryption='AES256'  # Enable encryption on backup
        )
        
        print(f"Copy operation completed successfully")
        print(f"  ETag: {copy_response.get('CopyObjectResult', {}).get('ETag', 'N/A')}")
        
        # Prepare success notification
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
        success_message = format_success_message(
            object_key, file_size, source_bucket, backup_bucket, current_time
        )
        
        # Send success notification
        print(f"\nSending success notification via SNS...")
        sns_response = sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject='AWS Backup Success - File Replicated',
            Message=success_message
        )
        
        print(f"Notification sent successfully")
        print(f"  Message ID: {sns_response['MessageId']}")
        
        print("\n" + "=" * 60)
        print("BACKUP OPERATION COMPLETED SUCCESSFULLY")
        print("=" * 60)
        
        # Return success response
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Backup completed successfully',
                'source': f"{source_bucket}/{object_key}",
                'destination': f"{backup_bucket}/{object_key}",
                'size_bytes': file_size,
                'timestamp': current_time
            })
        }
        
    except KeyError as e:
        # Handle malformed event data
        error_msg = f"Invalid event structure - missing required field: {str(e)}"
        print(f"\nERROR: {error_msg}")
        print(f"Event structure: {json.dumps(event, indent=2)}")
        
        send_failure_notification(
            sns_topic_arn if 'sns_topic_arn' in locals() else None,
            error_msg,
            "Invalid Event Data"
        )
        
        raise
        
    except ValueError as e:
        # Handle configuration errors
        error_msg = f"Configuration error: {str(e)}"
        print(f"\nERROR: {error_msg}")
        
        send_failure_notification(
            sns_topic_arn if 'sns_topic_arn' in locals() else None,
            error_msg,
            "Configuration Error"
        )
        
        raise
        
    except Exception as e:
        # Handle all other errors
        error_msg = f"Backup operation failed: {str(e)}"
        error_type = type(e).__name__
        
        print(f"\nERROR: {error_msg}")
        print(f"Error Type: {error_type}")
        
        # Prepare detailed error notification
        failure_message = format_failure_message(
            error_msg,
            error_type,
            object_key if 'object_key' in locals() else 'Unknown',
            source_bucket if 'source_bucket' in locals() else 'Unknown',
            backup_bucket if 'backup_bucket' in locals() else 'Not configured'
        )
        
        # Attempt to send failure notification
        try:
            if 'sns_topic_arn' in locals() and sns_topic_arn:
                sns_client.publish(
                    TopicArn=sns_topic_arn,
                    Subject='AWS Backup FAILURE - Action Required',
                    Message=failure_message
                )
                print("Failure notification sent")
        except Exception as sns_error:
            print(f"Failed to send failure notification: {str(sns_error)}")
        
        print("\n" + "=" * 60)
        print("BACKUP OPERATION FAILED")
        print("=" * 60)
        
        # Re-raise the original exception
        raise


def format_success_message(
    object_key: str,
    file_size: int,
    source_bucket: str,
    backup_bucket: str,
    timestamp: str
) -> str:
    """
    Format a success notification message.
    
    Args:
        object_key: Name of the backed up file
        file_size: Size of the file in bytes
        source_bucket: Source S3 bucket name
        backup_bucket: Backup S3 bucket name
        timestamp: Timestamp of the operation
        
    Returns:
        str: Formatted success message
    """
    file_size_mb = file_size / (1024 * 1024)
    
    return f"""
BACKUP OPERATION SUCCESSFUL

File Details:
-------------
File Name: {object_key}
File Size: {file_size:,} bytes ({file_size_mb:.2f} MB)

Source Location:
---------------
Bucket: {source_bucket}
Region: us-east-1 (N. Virginia)

Backup Location:
---------------
Bucket: {backup_bucket}
Region: us-west-2 (Oregon)

Operation Details:
-----------------
Status: SUCCESS
Timestamp: {timestamp}
Encryption: AES256 (Server-side)

Your file has been successfully replicated to the backup region.
This provides protection against regional failures and data loss.

---
Automated AWS S3 Backup System
"""


def format_failure_message(
    error_msg: str,
    error_type: str,
    object_key: str,
    source_bucket: str,
    backup_bucket: str
) -> str:
    """
    Format a failure notification message.
    
    Args:
        error_msg: Error message describing the failure
        error_type: Type of exception that occurred
        object_key: Name of the file that failed to back up
        source_bucket: Source S3 bucket name
        backup_bucket: Backup S3 bucket name
        
    Returns:
        str: Formatted failure message
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    
    return f"""
BACKUP OPERATION FAILED - ACTION REQUIRED

Error Details:
-------------
Error Type: {error_type}
Error Message: {error_msg}
Timestamp: {timestamp}

File Information:
----------------
File Name: {object_key}
Source Bucket: {source_bucket}
Backup Bucket: {backup_bucket}

Troubleshooting Steps:
---------------------
1. Check CloudWatch Logs for detailed error information
2. Verify IAM role permissions (S3 read/write, SNS publish)
3. Confirm backup bucket exists and is accessible
4. Verify environment variables are configured correctly
5. Check Lambda function timeout settings

CloudWatch Log Group:
--------------------
/aws/lambda/S3AutoBackupFunction

For immediate assistance, review the Lambda function logs
in CloudWatch or contact your cloud administrator.

---
Automated AWS S3 Backup System
"""


def send_failure_notification(
    sns_topic_arn: str,
    error_msg: str,
    error_category: str
) -> None:
    """
    Send a failure notification via SNS.
    
    Args:
        sns_topic_arn: ARN of the SNS topic
        error_msg: Error message to include
        error_category: Category of the error
    """
    if not sns_topic_arn:
        print("Cannot send failure notification - SNS topic ARN not available")
        return
    
    try:
        message = f"""
BACKUP SYSTEM ERROR

Category: {error_category}
Error: {error_msg}
Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}

Please check CloudWatch logs for detailed information.
"""
        
        sns_client.publish(
            TopicArn=sns_topic_arn,
            Subject=f'AWS Backup System Error - {error_category}',
            Message=message
        )
    except Exception as e:
        print(f"Failed to send error notification: {str(e)}")