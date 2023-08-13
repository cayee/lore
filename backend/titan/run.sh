rm -rf index_faiss*
cp -r ../../index_faiss*
aws ecr get-login-password --region us-east-2 | docker login --username AWS --password-stdin 253413553580.dkr.ecr.us-east-2.amazonaws.com
docker build -t ask-titan:v001 .
docker tag ask-titan:v001 253413553580.dkr.ecr.us-east-2.amazonaws.com/llm-repo:latest
docker push 253413553580.dkr.ecr.us-east-2.amazonaws.com/llm-repo:latest
aws lambda update-function-code --region us-east-2 --function-name arn:aws:lambda:us-east-2:253413553580:function:askTitan2 --image-uri 253413553580.dkr.ecr.us-east-2.amazonaws.com/llm-repo:latest
