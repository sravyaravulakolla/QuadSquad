
from flask import Flask, request
import boto3
import json
from flask import Flask, request, jsonify
from flask import jsonify
import os
import time
from botocore.exceptions import ClientError
from flask import send_file
app = Flask(__name__)

s3 = boto3.client('s3')

@app.route('/upload', methods=['POST'])
def upload_file():
    S3_BUCKET = <YourBucketName>
    folder_name='zipfile/'
    file = request.files['file']

    if file:
        file_key=folder_name+file.filename
        # Upload the file to S3 bucket
        s3.upload_fileobj(file, S3_BUCKET, file_key)
        return 'File uploaded successfully.'

    return 'No file selected.'


@app.route("/check_result")
def check_result():
    bucket_name = <YourBucketName>
    file_key = 'result/r.txt'
    while True:
        try:
            s3.head_object(Bucket=bucket_name, Key=file_key)
            response = s3.get_object(Bucket='divyareddybucket', Key='result/r.txt')
            file_content = response['Body'].read().decode('utf-8')
            print(file_content)
            return file_content

        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                time.sleep(5)  # Delay for 5 seconds before the next search attempt
            else:
                return False  # An error occurred while checking the file availability, return False
        except Exception as e:
            print(f"Error reading text file from S3: {e}")
            return 'Error occurred while reading text file from S3'


@app.route('/delete_files', methods=['POST'])
def delete_files():
    try:
        bucket_name = <YourBucketName>
        folder_name = 'result/'

        # Create an S3 client using Boto3
        s3_client = boto3.client('s3')

        # List objects within the specified folder
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=folder_name)

        # Extract file keys to delete
        objects_to_delete = [{'Key': obj['Key']} for obj in response.get('Contents', []) if obj['Key'] != folder_name]

        if len(objects_to_delete) > 0:
            # Delete the objects
            s3_client.delete_objects(Bucket=bucket_name, Delete={'Objects': objects_to_delete})

        return jsonify({'message': 'Files in the folder deleted successfully.'})

    except Exception as e:
        return jsonify({'error': str(e)})


@app.route('/stop_ec2_inst', methods=['POST'])
def stop_ec2_instance():
    # Create an EC2 client using Boto3
    ec2_client = boto3.client('ec2')

    # Specify the instance ID of the EC2 instance you want to stop
    instance_id = <ID>
    try:
        # Call the stop_instances API method to stop the EC2 instance
        response = ec2_client.stop_instances(InstanceIds=[instance_id])
        print("Stopped")
        return response
    except Exception as e:
        print("Error")
        return response



@app.route('/')
def stop():
        return "<p> Hello <p/>"

if __name__ == '__main__':
    app.run()
