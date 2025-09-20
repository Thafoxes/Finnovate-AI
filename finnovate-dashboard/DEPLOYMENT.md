# Finnovate Dashboard Deployment Guide

## Overview
This guide covers the complete deployment process for the Finnovate Dashboard using AWS S3 and CloudFront.

## Prerequisites
- AWS CLI installed and configured
- Node.js and npm installed
- Appropriate AWS permissions for S3, CloudFormation, and CloudFront

## Deployment Architecture
```
Internet → CloudFront CDN → S3 Static Website → React App
                ↓
            API Gateway → Lambda Functions → DynamoDB
```

## Environment Configuration

### Development
- File: `.env.development`
- Purpose: Local development with debug features
- API: Development/staging endpoints

### Staging
- File: `.env.staging`
- Purpose: Pre-production testing
- API: Staging endpoints with production-like data

### Production
- File: `.env.production`
- Purpose: Live production environment
- API: Production endpoints

## Deployment Scripts

### 1. Production Deployment
```bash
deploy.bat
```
- Builds production bundle
- Creates/updates CloudFormation stack
- Uploads to S3
- Invalidates CloudFront cache
- Opens deployed website

### 2. Staging Deployment
```bash
deploy-staging.bat
```
- Builds staging bundle
- Deploys to separate staging infrastructure
- Useful for testing before production

### 3. Health Check
```bash
health-check.bat
```
- Checks CloudFormation stack status
- Tests website accessibility
- Verifies CloudFront distribution
- Tests API endpoints

### 4. Rollback
```bash
rollback.bat
```
- Lists available backups
- Restores from selected backup
- Invalidates CloudFront cache

## Manual Deployment Steps

### Step 1: Build the Application
```bash
cd finnovate-dashboard
npm run build
```

### Step 2: Deploy Infrastructure
```bash
aws cloudformation create-stack \
  --stack-name finnovate-dashboard-infrastructure \
  --template-body file://aws-deployment.yaml \
  --parameters ParameterKey=BucketName,ParameterValue=finnovate-dashboard-prod \
  --region ap-southeast-1
```

### Step 3: Upload Files
```bash
aws s3 sync build/ s3://your-bucket-name --delete
```

### Step 4: Invalidate Cache
```bash
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

## Infrastructure Components

### S3 Bucket
- Static website hosting enabled
- Public read access configured
- CORS enabled for API calls
- Error pages redirect to index.html (SPA support)

### CloudFront Distribution
- Global CDN for fast content delivery
- HTTPS redirect enforced
- Caching optimized for static assets
- Custom error pages for SPA routing
- Security headers enabled

### CloudFormation Stack
- Infrastructure as Code
- Automated resource management
- Easy updates and rollbacks
- Output values for automation

## Performance Optimizations

### Build Optimizations
- Code splitting enabled
- Tree shaking for unused code
- Asset compression (gzip)
- Cache-busting with file hashes

### CloudFront Optimizations
- Managed caching policies
- Compression enabled
- HTTP/2 support
- Edge locations worldwide

### S3 Optimizations
- Static website hosting
- Efficient file organization
- Proper MIME types
- Cache headers

## Security Features

### CloudFront Security
- HTTPS enforcement
- Security headers policy
- Origin access control
- DDoS protection

### S3 Security
- Bucket policies for public read
- No public write access
- Access logging available
- Encryption at rest

## Monitoring and Logging

### CloudWatch Metrics
- CloudFront request metrics
- S3 bucket metrics
- Error rate monitoring
- Performance tracking

### Access Logs
- CloudFront access logs
- S3 access logs
- API Gateway logs
- Lambda function logs

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Node.js version compatibility
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

2. **Deployment Failures**
   - Verify AWS credentials
   - Check IAM permissions
   - Validate CloudFormation template

3. **Website Not Loading**
   - Check CloudFront distribution status
   - Verify S3 bucket policy
   - Check for cache issues

4. **API Errors**
   - Verify CORS configuration
   - Check API Gateway endpoints
   - Validate Lambda function logs

### Debug Commands
```bash
# Check stack status
aws cloudformation describe-stacks --stack-name finnovate-dashboard-infrastructure

# Check distribution status
aws cloudfront get-distribution --id YOUR_DISTRIBUTION_ID

# Test website
curl -I https://your-cloudfront-domain.com

# Check S3 sync
aws s3 ls s3://your-bucket-name --recursive
```

## Cost Optimization

### S3 Costs
- Use appropriate storage class
- Enable lifecycle policies
- Monitor data transfer

### CloudFront Costs
- Choose appropriate price class
- Monitor data transfer
- Optimize caching policies

### Estimated Monthly Costs
- S3 hosting: $1-5 (depending on traffic)
- CloudFront: $5-20 (depending on traffic)
- Total: $6-25/month for typical usage

## Backup and Recovery

### Automated Backups
- S3 versioning enabled
- CloudFormation stack exports
- Configuration backups

### Recovery Procedures
1. Use rollback.bat for quick recovery
2. Restore from S3 version history
3. Redeploy from source control

## CI/CD Integration

### GitHub Actions (Future)
```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS
on:
  push:
    branches: [main]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Node.js
        uses: actions/setup-node@v2
        with:
          node-version: '18'
      - name: Install dependencies
        run: npm install
      - name: Build
        run: npm run build
      - name: Deploy to AWS
        run: ./deploy.sh
```

## Support and Maintenance

### Regular Tasks
- Monitor CloudWatch metrics
- Update dependencies
- Review security settings
- Optimize performance

### Emergency Procedures
1. Use health-check.bat to diagnose issues
2. Use rollback.bat for quick recovery
3. Check AWS service health dashboard
4. Contact AWS support if needed

## Contact Information
- Project: Finnovate Dashboard
- Environment: Production
- Region: ap-southeast-1
- Support: Check AWS Console for real-time status