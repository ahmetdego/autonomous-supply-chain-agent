import boto3
import json
import tools  # Imports the tool definitions and mock functions

# --- AWS BEDROCK CONFIGURATION ---
# Initialize the Bedrock Runtime client to interact with the LLM.
# Ensure your AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY) are configured.
bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

# Model ID for Amazon Nova Micro (Efficient & Low Latency)
MODEL_ID = "amazon.nova-micro-v1:0" 

# --- SYSTEM PROMPT (THE AGENT'S BRAIN) ---
# This prompt defines the persona, specific rules, and financial logic.
SYSTEM_PROMPT = """
You are an Autonomous Enterprise Supply Chain Assistant.
Your goal is to optimize sales volume while strictly protecting PROFITABILITY.
Your boss is Mr. Ahmet. You must keep him informed via email for every action taken.

*** EXECUTION PROTOCOL & RULES ***

First, identify the REASON you were triggered (e.g., "Low Stock" or "Price Disadvantage"). 
You MUST ONLY take actions related to the specific trigger. Do not mix scenarios.

1. **IF TRIGGERED BY "Low Stock":**
   - Check the current 'stock_level'.
   - IF stock < 1500:
     - ACTION: Call 'create_restock_order' immediately.
     - NOTIFICATION: Send an email to Mr. Ahmet with the PO Number.
   - STRICT GUARDRAIL: DO NOT change the product price during a stockout anomaly. Leave the price exactly as it is. Do not execute price analysis.

2. **IF TRIGGERED BY "Price Disadvantage":**
   - Retrieve 'current_price', 'competitor_price', and 'cost_price'.
   - Calculate Floor Price = 'cost_price' * 1.10 (Maintain a 10% Profit Margin).
   - Calculate Target Price = 'competitor_price' - 1.
   
   - SCENARIO 2A: Profitable Competition
     - IF Target Price >= Floor Price:
     - ACTION: Update price to Target Price immediately.
     - EMAIL: "Mr. Ahmet, I undercut the competitor to [Target Price]. We remain profitable."
     
   - SCENARIO 2B: Profit Protection (Guardrail)
     - IF Target Price < Floor Price:
     - ACTION: Set price to Floor Price. NEVER go below this limit.
     - EMAIL: "Mr. Ahmet, the competitor's price is predatory. I held our price at the Floor Price ([Floor Price]) to protect margins."

3. **MANDATORY REPORTING**:
   - Send an email using 'send_notification_email' summarizing ONLY the actions you took for the specific trigger.
"""

def lambda_handler(event, context):
    """
    Main entry point for the Lambda function.
    It orchestrates the conversation with AWS Bedrock and handles Tool Execution (ReAct Pattern).
    """
    print("🧠 [BRAIN] Agent Activated. Analyzing Market Conditions...")
    
    # Simulating a trigger from the Dashboard/User
    # In a real scenario, this 'text' could come from the 'event' object.
    trigger_reason = event.get("trigger_reason", "Genel Kontrol")
    
    user_input = f"""
    Analyze product: 'OTC_VIT_C_ZINC'.
    
    CRITICAL TRIGGER REASON: '{trigger_reason}'
    
    INSTRUCTION: You MUST ONLY execute the rules defined in the SYSTEM PROMPT for this specific trigger reason. Do not perform general analysis. Execute necessary actions and send the notification email.
    """
    
    # Initialize conversation history
    messages = [{"role": "user", "content": [{"text": user_input}]}]


    

    
    turn_count = 0
    max_turns = 10  # Prevent infinite loops
    
    # --- AGENT LOOP (Reasoning + Acting) ---
    while turn_count < max_turns:
        turn_count += 1
        try:
            # 1. INVOKE MODEL (THINK)
            response = bedrock.converse(
                modelId=MODEL_ID,
                messages=messages,
                system=[{"text": SYSTEM_PROMPT}],
                toolConfig={"tools": tools.tool_config} # Inject available tools
            )
            
            # Parse response
            stop_reason = response['stopReason']
            message_content = response['output']['message']
            
            # Add model's response to history
            messages.append(message_content)

            # 2. EXECUTE TOOLS (ACT)
            if stop_reason == "tool_use":
                tool_requests = message_content['content']
                tool_results = []
                
                print(f"   🤖 [AGENT] Model requested {len(tool_requests)} tool(s)...")

                for content in tool_requests:
                    if 'toolUse' in content:
                        tool_use = content['toolUse']
                        tool_id = tool_use['toolUseId']
                        tool_name = tool_use['name']
                        tool_inputs = tool_use['input']
                        
                        # Execute the corresponding Python function from tools.py
                        result_data = tools.execute_tool_router(tool_name, tool_inputs)
                        
                        # Log specific actions for debugging
                        if tool_name == "send_notification_email":
                             print(f"   📧 [AGENT] Email Notification Dispatched.")

                        # Prepare result for the model
                        tool_results.append({
                            "toolResult": {
                                "toolUseId": tool_id,
                                "content": [{"json": result_data}]
                            }
                        })
                
                # Send tool results back to the model so it can formulate the final answer
                messages.append({"role": "user", "content": tool_results})
            
            # 3. FINAL ANSWER
            elif stop_reason == "end_turn":
                # The model has finished its task
                final_res = message_content['content'][0]['text']
                return {
                    'statusCode': 200, 
                    'body': json.dumps(final_res)
                }
                
        except Exception as e:
            print(f"❌ [ERROR] Agent crashed: {str(e)}")
            return {
                'statusCode': 500, 
                'body': json.dumps(f"Internal Error: {str(e)}")
            }

    return {'statusCode': 200, 'body': "Max turns reached"}