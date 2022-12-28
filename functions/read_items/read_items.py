import boto3
import os
import json

client = boto3.client('dynamodb')


def handler(event, context):
    data = client.get_item(
        TableName=os.environ['DYNAMODB_TABLE'],
        Key={
            'id': {
                'S': '005'
            }
        }
    )

    response = {
        'statusCode': 200,
        'body': json.dumps(data),
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
    }

    return response
