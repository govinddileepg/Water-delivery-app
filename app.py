# --- APP LAYOUT (SAFE MULTI-VIEW LOGIC) ---
st.title("💧 Water Drop Delivery")

if "auth_action" not in st.session_state:
    st.session_state["auth_action"] = "Sign In"

# Render 3 toggle buttons across the top header
col_btn1, col_btn2, col_btn3 = st.columns(3)
with col_btn1:
    if st.button("🔐 Go to Sign In", use_container_width=True, type="secondary" if st.session_state["auth_action"] != "Sign In" else "primary"):
        st.session_state["auth_action"] = "Sign In"
        st.rerun()
with col_btn2:
    if st.button("📝 Create Account", use_container_width=True, type="secondary" if st.session_state["auth_action"] != "Create Account" else "primary"):
        st.session_state["auth_action"] = "Create Account"
        st.rerun()
with col_btn3:
    if st.button("🔑 Forgot Password", use_container_width=True, type="secondary" if st.session_state["auth_action"] != "Forgot Password" else "primary"):
        st.session_state["auth_action"] = "Forgot Password"
        st.rerun()

st.markdown("---")

# ========================================================
# RENDER VIEW BASED ON SELECTION
# ========================================================

if st.session_state["auth_action"] == "Sign In":
    fields = {"Form name": "Login", "Username": "Username", "Password": "Password", "Login": "Login"}
    name, authentication_status, username = authenticator.login(location='main', fields=fields)

    if authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.info('Please enter your details to sign in.')
    elif authentication_status:
        user_info = credentials['usernames'][username]
        user_role = user_info['role']
        flat_no = user_info['flat_number']
        
        st.sidebar.write(f"Welcome, **{name}**")
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.markdown("---")

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

elif st.session_state["auth_action"] == "Create Account":
    st.subheader("New Resident Registration")
    new_name = st.text_input("Full Name", key="reg_name")
    new_username = st.text_input("Choose a Username", key="reg_user")
    new_flat = st.text_input("Flat Number (e.g., 27D, 4B)", key="reg_flat")
    new_password = st.text_input("Create Password", type="password", key="reg_pass")
    
    if st.button("Register Now", type="primary"):
        if not new_name or not new_username or not new_flat or not new_password:
            st.error("Please fill out all fields!")
        else:
            cursor.execute("SELECT username FROM users WHERE username = ?", (new_username,))
            if cursor.fetchone():
                st.error("Username already exists! Please pick another one.")
            else:
                cursor.execute(
                    "INSERT INTO users (username, name, password, role, flat_number) VALUES (?, ?, ?, ?, ?)",
                    (new_username, new_name, new_password, "Resident", new_flat)
                )
                conn.commit()
                st.success("Account created successfully! Tap 'Go to Sign In' above to access your profile.")
                st.balloons()

# ========================================================
# NEW: PASSWORD RESET / FORGOT WIDGET
# ========================================================
elif st.session_state["auth_action"] == "Forgot Password":
    try:
        # Render the built-in forgot password form layout
        forgot_fields = {'Form name': 'Reset Forgotten Password', 'Username': 'Enter Your Username', 'Submit': 'Generate New Password'}
        forgot_user, forgot_email, new_random_password = authenticator.forgot_password(location='main', fields=forgot_fields)
        
        if forgot_user:
            # Update the database with the newly generated temporary password string
            cursor.execute("UPDATE users SET password = ? WHERE username = ?", (new_random_password, forgot_user))
            conn.commit()
            
            st.warning("⚠️ Write down your temporary password immediately!")
            st.code(new_random_password, language="text")
            st.success("Database successfully updated! Click 'Go to Sign In' above and use this temporary password to enter.")
        elif forgot_user == False:
            st.error('Username not found in the resident directory.')
    except Exception as e:
        st.error(f"Execution Error: {e}")