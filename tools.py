import boto3
import json
import random
from decimal import Decimal

# --- CONFIGURATION ---
# region selection for AWS -- default eu-west-1
REGION = 'eu-west-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
table = dynamodb.Table('pharma_products')

# --- HELPERS ---
class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

# --- CORE FUNCTIONS ---

def get_product_market_data(product_id):
    """Fetches real-time product data from DynamoDB."""
    print(f"   🔧 [TOOLS] Fetching Data: {product_id}")
    try:
        response = table.get_item(Key={'drug_id': product_id})
        if 'Item' in response:
            return json.dumps(response['Item'], cls=DecimalEncoder)
        else:
            return json.dumps({"error": "Product not found"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def update_product_price(product_id, new_price, reason):
    """Updates the product price in the database."""
    print(f"   🔧 [TOOLS] Updating Price: {new_price} (Reason: {reason})")
    try:
        table.update_item(
            Key={'drug_id': product_id},
            UpdateExpression="set current_price = :p",
            ExpressionAttributeValues={':p': Decimal(str(new_price))}
        )
        return json.dumps({"status": "success", "message": "Price updated successfully"})
    except Exception as e:
        return json.dumps({"error": str(e)})

def create_restock_order(product_id, quantity):
    """Simulates placing a restock order with a supplier."""
    po_number = f"PO{random.randint(10000, 99999)}"
    supplier = "Global Pharma Logistics Ltd."
    
    print(f"   🔧 [TOOLS] Placing Order #{po_number} for {quantity} Units")
    try:
        table.update_item(
            Key={'drug_id': product_id},
            UpdateExpression="set stock_level = stock_level + :q",
            ExpressionAttributeValues={':q': Decimal(str(quantity))}
        )
        return json.dumps({
            "status": "success", 
            "message": "Order placed", 
            "po_details": {"po_number": po_number, "supplier": supplier}
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

def send_notification_email(subject, body, recipient="executive@enterprise.com"):
    """
    Simulates an Enterprise Email Service.
    In a production environment, this would be replaced by AWS SES (boto3).
    """
    print(f"   📧 [TOOLS] SIMULATING EMAIL TO {recipient}...")
    
    # Profesyonel görünen log formatı
    email_log = f"""
    ================ [ 📧 PRIORITY NOTIFICATION ] ================
    TO: {recipient}
    FROM: Autonomous_Supply_Chain_Agent
    SUBJECT: {subject}
    --------------------------------------------------------------
    {body}
    --------------------------------------------------------------
    [System: Delivered via Internal Secure Relay]
    ==============================================================
    """
    return json.dumps({"status": "email_sent", "content": email_log})

# --- TOOL ROUTER ---
def execute_tool_router(tool_name, inputs):
    """Routes the LLM's request to the correct Python function."""
    if tool_name == "get_product_market_data":
        return json.loads(get_product_market_data(inputs['product_id']))
    elif tool_name == "update_product_price":
        return json.loads(update_product_price(inputs['product_id'], inputs['new_price'], inputs['reason']))
    elif tool_name == "create_restock_order":
        return json.loads(create_restock_order(inputs['product_id'], inputs['quantity']))
    elif tool_name == "send_notification_email":
        # Recipient inputtan gelmezse varsayılan kullanılır
        return json.loads(send_notification_email(inputs['subject'], inputs['body']))
    return {"error": "Unknown tool"}

# --- TOOL CONFIGURATION (JSON Schema for Bedrock) ---
tool_config = [
    {
        "toolSpec": {
            "name": "get_product_market_data",
            "description": "Retrieves live market data (price, stock, competitor info) for a product.",
            "inputSchema": {"json": {"type": "object", "properties": {"product_id": {"type": "string"}}, "required": ["product_id"]}}
        }
    },
    {
        "toolSpec": {
            "name": "update_product_price",
            "description": "Updates the selling price of a product.",
            "inputSchema": {"json": {"type": "object", "properties": {"product_id": {"type": "string"}, "new_price": {"type": "number"}, "reason": {"type": "string"}}, "required": ["product_id", "new_price", "reason"]}}
        }
    },
    {
        "toolSpec": {
            "name": "create_restock_order",
            "description": "Places a purchase order (PO) to restock inventory.",
            "inputSchema": {"json": {"type": "object", "properties": {"product_id": {"type": "string"}, "quantity": {"type": "integer"}}, "required": ["product_id", "quantity"]}}
        }
    },
    {
        "toolSpec": {
            "name": "send_notification_email",
            "description": "Sends a formal notification email to the executive/boss.",
            "inputSchema": {"json": {"type": "object", "properties": {"subject": {"type": "string"}, "body": {"type": "string"}}, "required": ["subject", "body"]}}
        }
    }
]