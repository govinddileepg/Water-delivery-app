import streamlit as st
import sqlite3
import streamlit_authenticator as stauth
from datetime import datetime

# --- DATABASE SETUP ---
conn = sqlite3.connect("water_delivery.db", check_same_thread=False)
cursor = conn.cursor()

# 1. Orders Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flat_number TEXT,
    quantity INTEGER,
    timestamp TEXT,
    status TEXT
)
""")

# 2. Users Table (NEW: To store sign-ups dynamically)
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    name TEXT,
    password TEXT,
    role TEXT,
    flat_number TEXT
)
""")
conn.commit()

# --- PRE-POPULATE VENDOR (If table is brand new) ---
# This ensures our delivery guy Ramesh can always log in
cursor.execute("SELECT * FROM users WHERE username = 'water_vendor'")
if not cursor.fetchone():
    vendor_password = stauth.Hasher(['delivery123']).generate()[0]
    cursor.execute(
        "INSERT INTO users (username, name, password, role, flat_number) VALUES (?, ?, ?, ?, ?)",
        ("water_vendor", "Ramesh (Delivery)", vendor_password, "Vendor", "N/A")
    )
    conn.commit()

# --- LOAD USERS DYNAMICALLY FROM DATABASE ---
cursor.execute("SELECT username, name, password, role, flat_number FROM users")
db_users = cursor.fetchall()

# Reconstruct the credentials dictionary for the authenticator dynamically
credentials = {"usernames": {}}
for user in db_users:
    username, name, hashed_password, role, flat_no = user
    credentials["usernames"][username] = {
        "name": name,
        "password": hashed_password,
        "role": role,
        "flat_number": flat_no
    }

# Initialize the authenticator component
authenticator = stauth.Authenticate(
    credentials,
    "water_delivery_cookie",
    "abcdef",
    cookie_expiry_days=30
)

# --- APP LAYOUT (LOGIN & SIGN UP TABS) ---
st.title("💧 Water Drop Delivery")

# Create tabs so the login screen doesn't get cluttered
tab1, tab2 = st.tabs(["🔐 Sign In", "📝 Create Account"])

with tab1:
    # Render Login Interface
    fields = {"Form name": "Login", "Username": "Username", "Password": "Password", "Login": "Login"}
    name, authentication_status, username = authenticator.login(location='main', fields=fields)

with tab2:
    st.subheader("New Resident Registration")
    new_name = st.text_input("Full Name", key="reg_name")
    new_username = st.text_input("Choose a Username", key="reg_user")
    new_flat = st.text_input("Flat Number (e.g., 27D, 4B)", key="reg_flat")
    new_password = st.text_input("Create Password", type="password", key="reg_pass")
    
    if st.button("Register Now", type="primary"):
        if not new_name or not new_username or not new_flat or not new_password:
            st.error("Please fill out all fields!")
        else:
            # Check if username is already taken
            cursor.execute("SELECT username FROM users WHERE username = ?", (new_username,))
            if cursor.fetchone():
                st.error("Username already exists! Please pick another one.")
            else:
                # Hash the password and save to SQLite
                hashed_reg_password = stauth.Hasher([new_password]).generate()[0]
                cursor.execute(
                    "INSERT INTO users (username, name, password, role, flat_number) VALUES (?, ?, ?, ?, ?)",
                    (new_username, new_name, hashed_reg_password, "Resident", new_flat)
                )
                conn.commit()
                st.success("Account created successfully! You can now switch to the 'Sign In' tab.")
                st.balloons()

# ========================================================
# LOGIC BLOCK FOR AUTHENTICATED USERS
# ========================================================
if authentication_status == False:
    st.error('Username/password is incorrect')

elif authentication_status == None:
    st.info('Please sign in or create an account to place orders.')

elif authentication_status:
    # Pull current logged-in user details
    user_info = credentials['usernames'][username]
    user_role = user_info['role']
    flat_no = user_info['flat_number']
    
    st.sidebar.write(f"Welcome, **{name}**")
    authenticator.logout('Logout', 'sidebar')
    st.sidebar.markdown("---")

    # ==========================================
    # VIEW 1: RESIDENT DASHBOARD
    # ==========================================
    if user_role == "Resident":
        st.header("Place Your Order")
        st.info(f"Logged in profile auto-locked to: **Flat {flat_no}**")
        
        qty = st.number_input("Number of 20L Jars Needed", min_value=1, max_value=10, value=1)

        if st.button("🚀 Order Now", type="primary"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                "INSERT INTO orders (flat_number, quantity, timestamp, status) VALUES (?, ?, ?, ?)",
                (flat_no, qty, now, "Pending")
            )
            conn.commit()
            st.success(f"Success! Ordered {qty} jar(s).")

    # ==========================================
    # VIEW 2: VENDOR DASHBOARD
    # ==========================================
    elif user_role == "Vendor":
        st.header("📦 Vendor Dashboard")
        
        JAR_PRICE = 4.00 
        cursor.execute("SELECT SUM(quantity) FROM orders WHERE status = 'Completed'")
        total_jars_delivered = cursor.fetchone()[0] or 0
        total_earnings = total_jars_delivered * JAR_PRICE

        col_m1, col_m2 = st.columns(2)
        col_m1.metric(label="Total Jars Delivered", value=total_jars_delivered)
        col_m2.metric(label="Total Earnings", value=f"${total_earnings:,.2f}")
        
        st.markdown("---")
        st.subheader("Active Tasks")

        cursor.execute("SELECT id, flat_number, quantity, timestamp FROM orders WHERE status = 'Pending' ORDER BY id ASC")
        pending_orders = cursor.fetchall()

        if not pending_orders:
            st.info("🎉 All caught up! No pending orders right now.")
        else:
            for order in pending_orders:
                order_id, flat, quantity, order_time = order
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"### **Flat {flat}**")
                        st.markdown(f"**Quantity:** {quantity} Jar(s) | *Ordered at: {order_time}*")
                    with col2:
                        if st.button("Mark Delivered", key=f"del_{order_id}", type="secondary"):
                            cursor.execute("UPDATE orders SET status = 'Completed' WHERE id = ?", (order_id,))
                            conn.commit()
                            st.rerun()