from argparse import ArgumentParser

import boto3
import hyp3_sdk
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError

S3 = boto3.resource('s3')


def object_exists(bucket, key):
    try:
        S3.Object(bucket, key).load()
    except ClientError:
        return False
    return True


def copy_object(source_bucket, source_key, target_bucket, target_key, chunk_size=104857600):
    print(f'copying {source_bucket + "/" + source_key} to {target_bucket + "/" + target_key}')
    bucket = S3.Bucket(target_bucket)
    copy_source = {'Bucket': source_bucket, 'Key': source_key}
    transfer_config = TransferConfig(multipart_threshold=chunk_size, multipart_chunksize=chunk_size)
    bucket.copy(CopySource=copy_source, Key=target_key, Config=transfer_config)


def main():
    hyp3 = hyp3_sdk.HyP3(prompt=True)
    project_name = input('HyP3 project name: ')
    target_bucket = input('Destination bucket: ')

    jobs = hyp3.find_jobs(name=project_name)
    print(f'\nProject {project_name}: {jobs}')

    print('\nLooking for new files to copy...')

    objects_to_copy = []
    for job in jobs:
        source_bucket = job.files[0]['s3']['bucket']
        zip_key = job.files[0]['s3']['key']
        for ext in ('_VV.tif', '_VH.tif', '_rgb.tif', '_VV.tif.xml'):
            source_key = zip_key.replace('.zip', ext)
            target_key = source_key.replace(job.job_id, job.name)
            if not object_exists(target_bucket, target_key):
                objects_to_copy.append({
                    'source_bucket': source_bucket,
                    'source_key': source_key,
                    'target_bucket': target_bucket,
                    'target_key': target_key,
                })

    print(f'\nFound {len(objects_to_copy)} new files to copy to s3://{target_bucket}/{project_name}/')
    input('Press Enter to continue, Ctrl-c to cancel')

    for object_to_copy in objects_to_copy:
        copy_object(**object_to_copy)


if __name__ == '__main__':
    main()
