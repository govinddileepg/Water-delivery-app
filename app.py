import streamlit as st
import sqlite3
import streamlit_authenticator as stauth
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect("water_delivery.db", check_same_thread=False)
cursor = conn.cursor()
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

# --- AUTHENTICATION CONFIGURATION ---
# Define our users, passwords, and roles
credentials = {
    "usernames": {
        "john_doe": {
            "name": "John Doe (Flat 4B)",
            "password": "hashed_password_1", # Pre-hashed below
            "role": "Resident"
        },
        "water_vendor": {
            "name": "Ramesh (Delivery)",
            "password": "hashed_password_2", # Pre-hashed below
            "role": "Vendor"
        }
    }
}

# Plaintext passwords for this prototype: 
# john_doe -> "resident123"
# water_vendor -> "delivery123"
# Temporary simple text approach to get you past the crash:
credentials['usernames']['john_doe']['password'] = 'resident123'
credentials['usernames']['water_vendor']['password'] = 'delivery123'

# Initialize the authenticator component
authenticator = stauth.Authenticate(
    credentials,
    "water_delivery_cookie",
    "abcdef",
    cookie_expiry_days=30
)

# --- RENDER LOGIN INTERFACE ---
# We explicitly tell it to render on the main page, not the sidebar
fields = {"Form name": "Login", "Username": "Username", "Password": "Password", "Login": "Login"}
name, authentication_status, username = authenticator.login(location='main', fields=fields)

# ========================================================
# LOGIC BLOCK BASED ON LOGIN STATUS
# ========================================================

if authentication_status == False:
    st.error('Username/password is incorrect')

elif authentication_status == None:
    st.warning('Please enter your username and password')

elif authentication_status:
    # Successfully logged in! 
    # Show user info and a logout button in the sidebar
    user_role = credentials['usernames'][username]['role']
    st.sidebar.write(f"Welcome, **{name}**")
    authenticator.logout('Logout', 'sidebar')
    
    st.title("💧 Water Drop Delivery")
    st.sidebar.markdown("---")

    # ==========================================
    # VIEW 1: RESIDENT LOGIN
    # ==========================================
    if user_role == "Resident":
        st.header("Place Your Order")
        
        # Hardcoded flat number based on who logged in so they can't fake it!
        flat = "4B" if username == "john_doe" else "Unknown"
        st.info(f"Ordering for Apartment: **Flat {flat}**")
        
        qty = st.number_input("Number of 20L Jars Needed", min_value=1, max_value=10, value=1)

        if st.button("🚀 Order Now", type="primary"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO orders (flat_number, quantity, timestamp, status) VALUES (?, ?, ?, ?)",
                (flat, qty, now, "Pending")
            )
            conn.commit()
            st.success(f"Success! Ordered {qty} jar(s). The delivery guy has been notified.")

    # ==========================================
    # VIEW 2: VENDOR LOGIN
    # ==========================================
    elif user_role == "Vendor":
        st.header("📦 Active Delivery Tasks")

        cursor.execute("SELECT id, flat_number, quantity, timestamp FROM orders WHERE status = 'Pending' ORDER BY id ASC")
        pending_orders = cursor.fetchall()

        if not pending_orders:
            st.info("🎉 All caught up! No pending orders right now.")
        else:
            for order in pending_orders:
                order_id, flat_no, quantity, order_time = order
                
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### **Flat {flat_no}**")
                        st.markdown(f"**Quantity:** {quantity} Jar(s) | *Ordered at: {order_time}*")
                    with col2:
                        if st.button("Mark Delivered", key=f"del_{order_id}", type="secondary"):
                            cursor.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (order_id,))
                            conn.commit()
                            st.rerun()