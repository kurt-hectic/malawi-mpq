# run local docker image for testing
docker build -t s3tomqp . && docker run --rm -it -p 9000:8080 --env-file env_aws s3tomqp


curl -XPOST "http://localhost:9000/2015-03-31/functions/function/invocations" -d @test/s3-event.json