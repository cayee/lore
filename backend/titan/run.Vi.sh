docker build -t ask-titan-vi:v001 -f dockerfile.Vi .
docker tag ask-titan-vi:v001 253413553580.dkr.ecr.us-east-2.amazonaws.com/llm-repo:latest
docker push 253413553580.dkr.ecr.us-east-2.amazonaws.com/llm-repo:latest
aws lambda update-function-code --region us-east-2 --function-name arn:aws:lambda:us-east-2:253413553580:function:askTitanVi --image-uri 253413553580.dkr.ecr.us-east-2.amazonaws.com/llm-repo:latest --query State
