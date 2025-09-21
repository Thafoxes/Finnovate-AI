// Test script to verify CORS is working
console.log('Testing CORS for AI Conversation API...');

// Test 1: OPTIONS request (preflight)
fetch('https://59wn0kqhjl.execute-api.us-east-1.amazonaws.com/prod/ai/conversation', {
    method: 'OPTIONS',
    headers: {
        'Origin': 'http://localhost:3000',
        'Access-Control-Request-Method': 'POST',
        'Access-Control-Request-Headers': 'Content-Type'
    }
})
.then(response => {
    console.log('OPTIONS Response Status:', response.status);
    console.log('CORS Headers Present:');
    console.log('  Access-Control-Allow-Origin:', response.headers.get('Access-Control-Allow-Origin'));
    console.log('  Access-Control-Allow-Methods:', response.headers.get('Access-Control-Allow-Methods'));
    console.log('  Access-Control-Allow-Headers:', response.headers.get('Access-Control-Allow-Headers'));
    
    // Test 2: Actual POST request
    if (response.headers.get('Access-Control-Allow-Origin')) {
        console.log('CORS headers found! Testing POST request...');
        
        return fetch('https://59wn0kqhjl.execute-api.us-east-1.amazonaws.com/prod/ai/conversation', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: 'Hello AI! Can you help me with invoice management?',
                conversationId: 'test-cors-' + Date.now()
            })
        });
    } else {
        throw new Error('CORS headers not found in OPTIONS response');
    }
})
.then(response => {
    console.log('POST Response Status:', response.status);
    return response.text();
})
.then(data => {
    console.log('SUCCESS! API Response:', data);
    alert('CORS is working! API responded successfully. Check console for details.');
})
.catch(error => {
    console.error('CORS Test Failed:', error);
    alert('CORS test failed: ' + error.message);
});