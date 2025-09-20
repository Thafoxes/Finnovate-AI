@echo off
echo Quick Deploy Customer API Updates...

echo.
echo Building and deploying...
sam build && sam deploy

echo.
echo Deployment complete!
echo Check API Gateway console for new endpoints.
pause