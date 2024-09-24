import boto3
from common.methods import set_progress
from resourcehandlers.aws.models import AWSHandler

def run(job, *args, **kwargs):
    resource_handler_id = '{{ environmentName }}'
    bucket_name = '{{ bucketName }}'
    bucket_size = '{{ bucketSize }}'

    resource_handler = AWSHandler.objects.get(id=resource_handler_id)
    set_progress("Connecting to AWS s3...")
    s3 = boto3.client('s3', aws_access_key_id=resource_handler.serviceaccount,
                      aws_secret_access_key=resource_handler.servicepasswd)

    try:
        set_progress("Creating s3 bucket...")
        s3.create_bucket(Bucket=bucket_name)
        set_progress("Setting bucket size...")
        s3.put_bucket_lifecycle_configuration(
            Bucket=bucket_name,
            LifecycleConfiguration={
                'Rules': [
                    {
                        'ID': 'Set bucket size',
                        'Status': 'Enabled',
                        'Filter': {
                            'Prefix': ''
                        },
                        'NoncurrentVersionExpiration': {
                            'NoncurrentDays': bucket_size
                        }
                    },
                ]
            }
        )
        return "SUCCESS", f"Bucket {bucket_name} created successfully with size {bucket_size} GB", ""
    except Exception as err:
        return "FAILURE", "", f"Error creating bucket: {str(err)}"