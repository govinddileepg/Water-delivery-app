import streamlit as st
import sqlite3
from datetime import datetime

# --- DATABASE SETUP ---
# Connect to SQLite database (creates a file named water_delivery.db automatically)
conn = sqlite3.connect("water_delivery.db", check_same_thread=False)
cursor = conn.cursor()

# Create the orders table if it doesn't exist yet
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flat_number TEXT,
    quantity INTEGER,
    timestamp TEXT,
    status TEXT
)
""")
conn.commit()

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Water Drop", page_icon="💧", layout="centered")
st.title("💧 Water Drop Delivery")

# --- USER SELECTION ---
# Simulating a login switch for prototyping purposes
user_role = st.sidebar.radio("Select View Role:", ["Resident (Customer)", "Delivery Vendor"])

st.sidebar.markdown("---")
st.sidebar.caption("Prototype version 1.0 • Running on SQLite")

# ==========================================
# VIEW 1: RESIDENT SCREEN
# ==========================================
if user_role == "Resident (Customer)":
    st.header("Place Your Order")
    st.write("Need water? Select your flat and quantity below to notify the delivery team.")

    # Form inputs
    flat = st.text_input("Apartment / Flat Number (e.g., 4B, 12A)", placeholder="Enter Flat No.")
    qty = st.number_input("Number of 20L Jars Needed", min_value=1, max_value=10, value=1)

    if st.button("🚀 Order Now", type="primary"):
        if flat.strip() == "":
            st.error("Please enter your flat number before ordering!")
        else:
            # Insert order into SQLite database
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO orders (flat_number, quantity, timestamp, status) VALUES (?, ?, ?, ?)",
                (flat, qty, now, "Pending")
            )
            conn.commit()
            
            st.success(f"Success! Ordered {qty} jar(s) for Flat {flat}. The delivery guy has been notified.")
            
            # --- OPTIONAL TWILIO CODE GOES HERE ---
            # base_whatsapp_function(flat, qty)

# ==========================================
# VIEW 2: DELIVERY VENDOR DASHBOARD
# ==========================================
elif user_role == "Delivery Vendor":
    st.header("📦 Active Delivery Tasks")
    st.write("Below are the pending water orders for your building.")

    # Fetch only 'Pending' orders from the database
    cursor.execute("SELECT id, flat_number, quantity, timestamp FROM orders WHERE status = 'Pending' ORDER BY id ASC")
    pending_orders = cursor.fetchall()

    if not pending_orders:
        st.info("🎉 All caught up! No pending orders right now.")
    else:
        # Loop through each pending order and display it cleanly
        for order in pending_orders:
            order_id, flat_no, quantity, order_time = order
            
            # Create a visual box for each order row
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"### **Flat {flat_no}**")
                    st.markdown(f"**Quantity:** {quantity} Jar(s) | *Ordered at: {order_time}*")
                
                with col2:
                    # Unique key required for dynamic button rendering in loops
                    if st.button("Mark Delivered", key=f"del_{order_id}", type="secondary"):
                        # Update status to completed in database
                        cursor.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (order_id,))
                        conn.commit()
                        st.rerun() # Refresh app interface to remove completed orders