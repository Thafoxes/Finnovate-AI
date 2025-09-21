from flask import Flask, jsonify, request
import json
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Simple CORS handling
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),  # Fixed deprecation warning
        "environment": "local",
        "aws_region": os.getenv('AWS_REGION', 'ap-southeast-1'),
        "bedrock_model": os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-micro-v1:0'),
        "aws_configured": bool(os.getenv('AWS_ACCESS_KEY_ID'))
    })

@app.route('/test-bedrock', methods=['GET'])
def test_bedrock():
    try:
        # Check if credentials are configured
        if not os.getenv('AWS_ACCESS_KEY_ID'):
            return jsonify({
                "status": "error",
                "message": "AWS credentials not configured",
                "suggestion": "Add AWS credentials to .env file"
            }), 400
        
        # For now, return mock success to test other parts
        return jsonify({
            "status": "mock_success",
            "message": "Bedrock connection mocked - AWS credentials found",
            "model_id": os.getenv('BEDROCK_MODEL_ID', 'amazon.nova-micro-v1:0'),
            "region": os.getenv('AWS_REGION', 'ap-southeast-1'),
            "note": "Real Bedrock testing disabled due to token expiry"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "suggestion": "Check AWS credentials and token expiry"
        }), 500

@app.route('/invoices', methods=['GET'])
def get_invoices():
    try:
        # Mock invoice data matching your CSV structure
        invoices = [
            {
                "invoice_id": "INV-2024-001",
                "customer_id": "CUST001",
                "customer_name": "Acme Corporation",
                "customer_email": "billing@acme.com",
                "total_amount": 1500.00,
                "currency": "USD",
                "status": "OVERDUE",
                "due_date": "2024-01-15",
                "issue_date": "2024-01-01",
                "days_overdue": 15
            },
            {
                "invoice_id": "INV-2024-002", 
                "customer_id": "CUST002",
                "customer_name": "TechStart Inc",
                "customer_email": "finance@techstart.com",
                "total_amount": 3200.00,
                "currency": "USD",
                "status": "PAID",
                "due_date": "2024-01-20",
                "issue_date": "2024-01-05",
                "days_overdue": 0
            }
        ]
        
        return jsonify({
            "success": True,
            "count": len(invoices),
            "invoices": invoices
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Invoice retrieval error: {str(e)}"
        }), 500

@app.route('/invoices/overdue', methods=['GET'])
def get_overdue_invoices():
    try:
        overdue_invoices = [
            {
                "invoice_id": "INV-2024-001",
                "customer_id": "CUST001",
                "customer_name": "Acme Corporation",
                "customer_email": "billing@acme.com", 
                "total_amount": 1500.00,
                "currency": "USD",
                "days_overdue": 15,
                "due_date": "2024-01-15",
                "priority": "high"
            }
        ]
        
        return jsonify({
            "success": True,
            "count": len(overdue_invoices),
            "overdue_invoices": overdue_invoices
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Overdue invoice retrieval error: {str(e)}"
        }), 500

@app.route('/ai/chat', methods=['POST'])
def ai_chat():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
            
        message = data.get('message', '')
        
        # Mock intelligent responses based on message content
        if 'overdue' in message.lower():
            response = "I found 1 overdue invoice: INV-2024-001 from Acme Corporation for $1,500, which is 15 days overdue. Would you like me to generate a payment reminder email?"
        elif 'payment reminder' in message.lower() or 'email' in message.lower():
            response = "I can generate a professional payment reminder email. Based on the customer's payment history, I recommend a firm but polite tone. Should I proceed with generating the email?"
        elif 'payment history' in message.lower():
            response = "Acme Corporation's payment history: 3 invoices paid on time, 2 late payments (average 8 days delay). Current risk level: Medium. Outstanding balance: $1,500."
        elif 'strategy' in message.lower() or 'collection' in message.lower():
            response = "For this customer, I recommend: 1) Send formal reminder immediately, 2) Follow up in 7 days with payment plan options, 3) Consider phone call after 30 days total overdue."
        else:
            response = f"I understand you're asking about: '{message}'. I can help with overdue invoice analysis, payment reminder generation, customer payment history, and collection strategies. What would you like to focus on?"
        
        return jsonify({
            "response": response,
            "context": "payment_management",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "mock_ai"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"AI chat error: {str(e)}",
            "message": "Error processing chat request"
        }), 500

@app.route('/ai/generate-email', methods=['POST'])
def generate_email():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        customer_name = data.get('customer_name', 'Valued Customer')
        invoice_id = data.get('invoice_id', 'N/A')
        amount = data.get('amount', 0)
        days_overdue = data.get('days_overdue', 0)
        tone = data.get('tone', 'professional')
        
        # Generate email based on parameters
        if tone == 'friendly' or days_overdue < 10:
            subject = f"Friendly Reminder: Invoice {invoice_id}"
            body = f"""Dear {customer_name},

I hope this message finds you well. This is a gentle reminder that invoice {invoice_id} for ${amount:,.2f} is currently {days_overdue} days overdue.

If you have already processed this payment, please disregard this message. If you have any questions or need assistance, please don't hesitate to reach out.

Thank you for your attention to this matter.

Best regards,
AI Payment Assistant"""
        
        elif tone == 'firm' or days_overdue >= 15:
            subject = f"Urgent: Payment Required for Invoice {invoice_id}"
            body = f"""Dear {customer_name},

Our records indicate that invoice {invoice_id} for ${amount:,.2f} is now {days_overdue} days overdue.

Please arrange payment immediately to avoid any service disruption. If you are experiencing difficulties, please contact us to discuss payment options.

Immediate attention to this matter is required.

Regards,
Accounts Receivable Team"""
        
        else:
            subject = f"Payment Reminder: Invoice {invoice_id}"
            body = f"""Dear {customer_name},

This is a reminder that invoice {invoice_id} for ${amount:,.2f} is {days_overdue} days overdue.

Please process payment at your earliest convenience. If you need assistance or have questions, please contact us.

Thank you,
Finance Department"""
        
        return jsonify({
            "subject": subject,
            "body": body,
            "tone": tone,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "mock_ai_generator"
        })
        
    except Exception as e:
        return jsonify({
            "error": f"Email generation error: {str(e)}"
        }), 500

@app.route('/campaigns', methods=['GET', 'POST'])
def campaigns():
    try:
        if request.method == 'GET':
            return jsonify({
                "success": True,
                "campaigns": [
                    {
                        "campaign_id": "CAMP-001",
                        "campaign_name": "Q1 Collection Drive", 
                        "status": "active",
                        "created_date": "2024-01-01",
                        "target_customers": 5,
                        "emails_sent": 12,
                        "responses_received": 3
                    }
                ]
            })
        else:
            data = request.get_json() or {}
            new_campaign = {
                "campaign_id": f"CAMP-{int(datetime.now().timestamp())}",
                "campaign_name": data.get('campaign_name', 'New Campaign'),
                "status": "created",
                "created_date": datetime.now(timezone.utc).isoformat()
            }
            return jsonify({
                "success": True,
                "campaign": new_campaign
            }), 201
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Campaign operation error: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("🚀 Simple AI Payment Intelligence Server")
    print("📡 Running at: http://localhost:5000")
    print("🎭 Using mock responses (no AWS dependencies)")
    print("✅ All endpoints functional")
    print("")
    app.run(debug=True, host='0.0.0.0', port=5000)