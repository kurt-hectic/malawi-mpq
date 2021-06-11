$bucketname = "test-bucket-wmo"
$username = "test-upload"
$userpolicyname = "test-allow_upload"

#create S3 bucket
aws s3 rm s3://$bucketname --recursive  
aws s3api delete-bucket --bucket $bucketname
aws iam delete-user-policy --user-name $username --policy-name $userpolicyname 

$json = aws iam list-access-keys --user-name test-upload | ConvertFrom-Json

aws iam delete-access-key --access-key-id $json.AccessKeyMetadata[0].AccessKeyId --user-name $username
aws iam delete-user --user-name $username


aws s3api create-bucket --bucket $bucketname --region eu-central-1 --create-bucket-configuration LocationConstraint=eu-central-1
aws s3api put-public-access-block --bucket $bucketname --public-access-block-configuration "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"
aws s3api put-object --bucket $bucketname --key incoming/
aws s3api put-object --bucket $bucketname --key public/


((Get-Content -path bucket-policy.json -Raw) -replace '#bucketname#',$bucketname) | Set-Content -Path bucket-policy-temp.json
aws s3api put-bucket-policy --bucket $bucketname --policy file://bucket-policy-temp.json
Remove-Item bucket-policy-temp.json


# create user for S3 upload

aws iam create-user --user-name $username 
aws iam create-access-key --user-name $username

((Get-Content -path user-policy.json -Raw) -replace '#bucketname#',$bucketname) | Set-Content -Path user-policy-temp.json
aws iam put-user-policy --user-name $username --policy-name $userpolicyname --policy-document file://user-policy-temp.json
Remove-Item user-policy-temp.json
