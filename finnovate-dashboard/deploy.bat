@echo off
echo Building production bundle...
npm run build

echo Uploading to S3...
aws s3 sync build/ s3://finnovate-dashboard-prod --delete

echo Creating CloudFront invalidation...
aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths "/*"

echo Deployment complete!
echo Website URL: https://YOUR_CLOUDFRONT_DOMAIN
pause