from common.methods import set_progress
from infrastructure.models import Environment
from infrastructure.models import CustomField
from infrastructure.models import Server
from orders.models import Order
from jobs.models import Job
from resources.models import Resource
from resources.models import ResourceType
from resourcehandlers.models import ResourceHandler
from servicecatalog.models import ServiceBlueprint
from owners.models import UserProfile
from owners.models import Group
import boto3

def run(job, *args, **kwargs):
    bucketName = "{{ bucketName }}"
    rhName = "{{ rhName }}"
    bucketSize = int("{{ bucketSize }}")
    try:
        for k,v in kwargs.items():
            set_progress(f"{k} is {v}")
            if k == 'blueprint_order_item':
                bpoi_id = v
                break
        if (bpoi_id):        
            order_id = Order.objects.get(id=bpoi_id).order_id
            order = Order.objects.get(id=order_id)
            owner = order.owner
            group = order.group
        else:
            return "FAILURE", "", "Blueprint order item not found"

        rh = ResourceHandler.objects.get(name=rhName)
        env = rh.environment_set.first()
        aws_region = env.aws_region

        session = boto3.Session(region_name=aws_region, aws_access_key_id=rh.serviceaccount, aws_secret_access_key=rh.servicepasswd)
        s3 = session.resource('s3')

        if aws_region == 'us-east-1':
            bucket = s3.create_bucket(Bucket=bucketName)
        else:
            bucket = s3.create_bucket(Bucket=bucketName, CreateBucketConfiguration={'LocationConstraint': aws_region})

        aws_s3_bucketsize, _ = CustomField.objects.get_or_create(
            name='aws_s3_bucketsize',
            defaults={
                "label": 'AWS S3 Bucket Size',
                "type": 'INT',
                "show_as_attribute": True,
                "show_on_objects": True,
            }
        )

        resource_type, _ = ResourceType.objects.get_or_create(
            name='aws_s3_bucket',
            defaults={'label': 'AWS S3 Bucket'}
        )

        resource = Resource.objects.create(
            name=bucketName,
            resource_type=resource_type,
            lifecycle='ACTIVE',
            blueprint_id=bpoi_id,
            group=group,
            owner=owner
        )

        resource.aws_s3_bucketsize = bucketSize
        resource.save()

        return "SUCCESS", f"Bucket {bucketName} created in region {aws_region}", ""
    except Exception as e:
        return "FAILURE", "", f"{e}"