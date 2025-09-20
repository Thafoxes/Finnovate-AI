@echo off
echo Deploying Customer API Updates...

echo.
echo Step 1: Building SAM application...
sam build

echo.
echo Step 2: Deploying to AWS...
sam deploy --guided

echo.
echo Deployment complete!
pause