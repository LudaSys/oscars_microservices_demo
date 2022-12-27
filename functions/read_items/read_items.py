import boto3
import json

client = boto3.client('dynamodb')

def handler(event, context):
    data = client.get_item(
    TableName='user_choices',
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