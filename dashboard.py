import streamlit as st
import boto3
import time
import json
import random
import os
from datetime import datetime
from decimal import Decimal


if "aws" in st.secrets:
    os.environ["AWS_ACCESS_KEY_ID"] = st.secrets["aws"]["access_key_id"]
    os.environ["AWS_SECRET_ACCESS_KEY"] = st.secrets["aws"]["secret_access_key"]
    os.environ["AWS_DEFAULT_REGION"] = st.secrets["aws"]["region"]


# IMPORT BRAIN (Local Lambda Function)
import lambda_function as agent_brain


# --- AWS CONFIGURATION ---
REGION = 'eu-west-1'
dynamodb = boto3.resource('dynamodb', region_name=REGION)
product_table = dynamodb.Table('pharma_products')
PRODUCT_ID = 'OTC_VIT_C_ZINC'

# --- SESSION STATE INITIALIZATION ---
if 'logs' not in st.session_state:
    st.session_state['logs'] = []
if 'run_simulation' not in st.session_state:
    st.session_state['run_simulation'] = False

# --- UI SETUP ---
st.set_page_config(page_title="Enterprise AI System", layout="wide", page_icon="⚡")
st.title("⚡ Autonomous Self-Healing Supply Chain")

col_main, col_logs = st.columns([2, 1])

# LOG PANEL (Global Access)
with col_logs:
    st.subheader("📜 System Logs & Notifications")
    log_placeholder = st.empty()

# --- HELPER FUNCTIONS ---

def render_logs():
    """Refreshes the log panel immediately."""
    log_text = "\n".join(st.session_state['logs'])
    log_placeholder.text_area("Console Output", value=log_text, height=750, key=f"log_{time.time()}")

def log_event(message, type="INFO"):
    """Logs events to both terminal and UI."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] [{type}] {message}"
    print(formatted_msg)
    st.session_state['logs'].append(formatted_msg)
    render_logs()

def get_product_state():
    """Fetches real-time data with Strong Consistency."""
    try:
        response = product_table.get_item(Key={'drug_id': PRODUCT_ID}, ConsistentRead=True)
        return response.get('Item', {})
    except Exception as e:
        log_event(f"Db Error: {e}", "ERROR")
        return {}

def trigger_ai_agent(reason):
    """Triggers the AI Brain."""
    log_event(f"🤖 AI AGENT TRIGGERED! Reason: {reason}", "AI-ACTION")
    
    with st.spinner('AI Agent is analyzing market & profitability...'):
        result = agent_brain.lambda_handler({"trigger_reason": reason}, {})
        
        if result['statusCode'] == 200:
            report = json.loads(result['body'])
            log_event(f"✅ ACTION REPORT: {report}", "AI-SUCCESS")
            return True
        else:
            log_event(f"❌ EXECUTION FAILED: {result['body']}", "AI-FAIL")
            return False

def update_stock(amount):
    """Simulates sales transaction."""
    try:
        product_table.update_item(
            Key={'drug_id': PRODUCT_ID},
            UpdateExpression="set stock_level = stock_level + :val",
            ExpressionAttributeValues={':val': Decimal(amount)}
        )
        return True
    except Exception as e:
        log_event(f"Update Error: {e}", "ERROR")
        return False

# --- MAIN UI LOGIC ---

with col_main:
    # METRICS SECTION
    metrics_placeholder = st.empty()
    
    def update_metrics_display():
        """Updates metrics immediately."""
        data = get_product_state()
        if data:
            with metrics_placeholder.container():
                c1, c2, c3, c4 = st.columns(4)
                
                # 1. Our Price
                my_price = data.get('current_price')
                c1.metric("Our Price", f"{my_price} TL")
                
                # 2. Competitor Price (Red if low)
                c2.metric("Competitor", f"{data.get('competitor_price')} TL", delta_color="inverse")
                
                # 3. Cost Limit (Profit Guardrail)
                cost = data.get('cost_price', 60)
                # Show Cost + 10% Margin
                limit = float(cost) * 1.1
                c3.metric("Cost Limit", f"{limit:.1f} TL", help="Minimum Profitable Price (Cost + 10%)")
                
                # 4. Stock Level
                stock = data.get('stock_level')
                c4.metric("Stock", f"{stock}", delta="-LOW" if stock < 1500 else "Safe")
                return data
        return {}

    # Initial Load
    current_data = update_metrics_display()
    st.divider()

    # CONTROL CENTER
    st.subheader("🎮 Operations Command Center")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        if st.button("▶️ START SMART-PILOT", type="primary", use_container_width=True):
            st.session_state['run_simulation'] = True
            log_event("Smart-Pilot Simulation Started...", "SYSTEM")
    
    with c2:
        if st.button("⏹️ STOP SIMULATION", type="secondary", use_container_width=True):
            st.session_state['run_simulation'] = False
            log_event("Simulation Stopped by User.", "SYSTEM")
            st.rerun()

    # --- SIMULATION LOOP ---
    if st.session_state['run_simulation']:
        status_text = st.empty()
        status_text.info("System Running... Optimizing for Profit...")
        
        for i in range(50):
            if not st.session_state['run_simulation']:
                status_text.warning("Stopped.")
                break
            
            # 1. Refresh Data
            data = update_metrics_display()
            my_price = float(data.get('current_price', 0))
            comp_price = float(data.get('competitor_price', 0))
            cost_price = float(data.get('cost_price', 60))
            floor_price = cost_price * 1.10 # %10 Margin
            stock = float(data.get('stock_level', 0))

            # 2. Sales Logic (The Smart Merchant)
            if my_price > comp_price:
                # If we are expensive, check if we are protecting margin
                # (Allow 1 unit buffer for floating point comparison)
                if my_price <= (floor_price + 1):
                     log_event(f"🛡️ PROFIT PROTECTION: Holding price at {my_price}. Refusing to sell at loss.", "HOLD")
                else:
                     log_event(f"⛔ SALES PAUSED: We are too expensive ({my_price} > {comp_price}). Waiting for AI...", "WARNING")
            else:
                # Price is competitive -> Sell!
                sale_amount = random.randint(50, 150) * -1
                update_stock(sale_amount)
                log_event(f"💰 Transaction: Sold {abs(sale_amount)} units.", "SALES")
            
            # 3. Guard Rails (Triggers)
            
            # Crisis A: Low Stock
            if stock < 1500:
                log_event(f"⚠️ Anomaly: Low Stock ({stock})", "ALERT")
                trigger_ai_agent("Low Stock")
                update_metrics_display() 
            
            # Crisis B: Price Disadvantage
            elif comp_price < my_price:
                log_event(f"⚠️ Anomaly: Price Disadvantage Detected", "ALERT")
                trigger_ai_agent("Price Disadvantage")
                update_metrics_display() 

            time.sleep(1.5)

    st.divider()
    
    # MANUAL TRIGGERS
    st.caption("Scenario Injection")
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        if st.button("📦 Simulate: Stockout", use_container_width=True):
            product_table.update_item(Key={'drug_id': PRODUCT_ID}, UpdateExpression="set stock_level=:s", ExpressionAttributeValues={':s': Decimal(50)})
            log_event("🚨 INJECTED: Critical Stockout (50 Units)", "CRISIS")
            st.rerun()

    with col_m2:
        # DROP COMPETITOR BY 20 EACH CLICK
        if st.button("📉 Simulate: Drop Competitor (-20 TL)", use_container_width=True):
            product_table.update_item(
                Key={'drug_id': PRODUCT_ID}, 
                UpdateExpression="set competitor_price = competitor_price - :val", 
                ExpressionAttributeValues={':val': Decimal(20)}
            )
            log_event("📉 INJECTED: Competitor dropped price by 20 TL", "CRISIS")
            st.rerun() # Instant Refresh
            
    with col_m3:
        if st.button("🔄 Factory Reset", use_container_width=True):
            product_table.update_item(
                Key={'drug_id': PRODUCT_ID},
                UpdateExpression="set stock_level=:s, current_price=:p, competitor_price=:cp",
                ExpressionAttributeValues={':s': Decimal(3000), ':p': Decimal(120), ':cp': Decimal(130)}
            )
            st.session_state['logs'] = []
            st.rerun()

render_logs()