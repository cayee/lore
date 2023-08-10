def lambda_handler(event, context):
    return {
        'statusCode': 302,
        'headers' : { 'Location': 'https://lore-poc.pwlkrz.people.aws.dev/ai/index.html' }
    }

