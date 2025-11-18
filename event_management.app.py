# event_management_app_safe.py
import streamlit as st
import mysql.connector
import pandas as pd
import traceback
from mysql.connector import Error

st.set_page_config(page_title="Event Management GUI (Safe)", layout="wide")

# --- Config (change these to match your environment) ---
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "charan17"   # <-- update
DB_NAME = "event5"

# --- Helper: show startup errors on UI so page isn't blank ---
def render_startup_error(e: Exception):
    st.title("⚠️ App failed to start")
    st.error("An exception occurred during startup. See details below.")
    st.code(traceback.format_exc(), language="python")
    st.stop()

# --- DB connection singleton so app doesn't repeatedly reconnect ---
@st.cache_resource
def get_connection():
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False
        )
        return conn
    except Exception as e:
        # re-raise so caller can display
        raise

# --- Safe query runner that surfaces errors on the page ---
def run_query(query, params=None, fetch=True):
    try:
        conn = get_connection()
    except Exception as e:
        st.error("Unable to connect to database. Check DB credentials / that MySQL is running.")
        st.exception(e)
        return None

    try:
        cur = conn.cursor(dictionary=True)
        cur.execute(query, params or ())
        if fetch:
            rows = cur.fetchall()
            cur.close()
            return rows
        else:
            conn.commit()
            cur.close()
            return True
    except Error as e:
        # Show MySQL error in UI (including trigger/constraint messages)
        st.error("MySQL Error:")
        st.write(str(e))
        # if detailed server message exists
        try:
            st.code(traceback.format_exc(), language="python")
        except:
            pass
        return None

# --- Test DB connection and ensure tables exist (run immediately so errors show) ---
try:
    conn_test = get_connection()
    with conn_test.cursor() as c:
        c.execute("SELECT COUNT(*) as c FROM information_schema.tables WHERE table_schema = %s;", (DB_NAME,))
        cnt = c.fetchone()
        # nothing else; close only if not needed later
except Exception as e:
    render_startup_error(e)

# --- UI: header and connection status ---
st.title("🎟️ Event Management GUI (Safe)")
st.sidebar.markdown("### Quick actions")
try:
    conn = get_connection()
    if conn.is_connected():
        st.sidebar.success(f"Connected to {DB_NAME}@{DB_HOST}")
    else:
        st.sidebar.warning("Not connected")
except Exception as e:
    st.sidebar.error("DB connection error")
    st.sidebar.write(str(e))

# --- Auth + simple session handling ---
if "user_id" not in st.session_state:
    st.session_state.user_id = None

def login_section():
    st.header("🔐 Login")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_pass")
    if st.button("Login"):
        try:
            conn = get_connection()
            cur = conn.cursor()
            cur.execute("SELECT check_login_credentials(%s, %s);", (email, password))
            res = cur.fetchone()
            cur.close()
            if res and res[0] != 0:
                st.success(f"Logged in as user_id={res[0]}")
                st.session_state.user_id = res[0]
            else:
                st.error("Invalid credentials (function returned 0).")
        except Error as e:
            st.error("Login error:")
            st.write(str(e))

def logout():
    st.session_state.user_id = None
    st.success("Logged out")

# --- Events management (insertion triggers DB triggers) ---
def manage_events():
    st.header("🎫 Events")
    with st.form("add_event", clear_on_submit=True):
        col1, col2 = st.columns(2)
        title = col1.text_input("Title")
        location = col1.text_input("Location")
        start_time = col2.text_input("Start time (YYYY-MM-DD HH:MM:SS)")
        end_time = col2.text_input("End time (YYYY-MM-DD HH:MM:SS)")
        description = st.text_area("Description")
        submitted = st.form_submit_button("Add Event")
        if submitted:
            if not st.session_state.user_id:
                st.error("You must login first.")
            else:
                q = """
                INSERT INTO events (title, description, location, start_time, end_time, user_id)
                VALUES (%s,%s,%s,%s,%s,%s)
                """
                ok = run_query(q, (title, description, location, start_time, end_time, st.session_state.user_id), fetch=False)
                if ok:
                    st.success("Event inserted (triggers run on DB).")

    # list events
    rows = run_query("SELECT * FROM events ORDER BY id DESC;")
    if rows is not None:
        df = pd.DataFrame(rows)
        if not df.empty:
            st.dataframe(df)
        else:
            st.info("No events yet.")

# --- Attendees, Vendors, Sponsors simple CRUD interfaces ---
def manage_attendees():
    st.header("🙋 Attendees")
    with st.form("add_att"):
        event_id = st.number_input("Event ID", min_value=1, step=1)
        email = st.text_input("Email")
        if st.form_submit_button("Add Attendee"):
            run_query("INSERT INTO attendees (event_id, email) VALUES (%s, %s);", (event_id, email), fetch=False)
            st.success("Attendee inserted.")
    data = run_query("SELECT * FROM attendees;")
    st.dataframe(pd.DataFrame(data) if data else pd.DataFrame())

def manage_vendors():
    st.header("🍽️ Vendors")
    with st.form("add_vendor"):
        event_id = st.number_input("Event ID", min_value=1, step=1, key="v_eid")
        name = st.text_input("Name", key="v_name")
        service = st.text_input("Service", key="v_service")
        amount = st.number_input("Amount to be paid", min_value=0.0, key="v_amount")
        if st.form_submit_button("Add Vendor"):
            run_query("INSERT INTO vendors (event_id, name, service, amount_to_be_paid) VALUES (%s,%s,%s,%s);",
                      (event_id, name, service, amount), fetch=False)
            st.success("Vendor added.")
    data = run_query("SELECT * FROM vendors;")
    st.dataframe(pd.DataFrame(data) if data else pd.DataFrame())

def manage_sponsors():
    st.header("💼 Sponsors")
    with st.form("add_sponsor"):
        event_id = st.number_input("Event ID", min_value=1, step=1, key="s_eid")
        name = st.text_input("Name", key="s_name")
        level = st.text_input("Level", key="s_level")
        contribution = st.number_input("Contribution", min_value=0.0, key="s_contribution")
        if st.form_submit_button("Add Sponsor"):
            run_query("INSERT INTO sponsors (event_id, name, level, contribution) VALUES (%s,%s,%s,%s);",
                      (event_id, name, level, contribution), fetch=False)
            st.success("Sponsor added.")
    data = run_query("SELECT * FROM sponsors;")
    st.dataframe(pd.DataFrame(data) if data else pd.DataFrame())

# --- Event summary using stored procedure ---
def event_summary():
    st.header("📊 Event Summary (stored procedure)")
    event_id = st.number_input("Event ID", min_value=1, step=1, key="sum_eid")
    if st.button("Get Summary"):
        try:
            conn = get_connection()
            cur = conn.cursor(dictionary=True)
            cur.callproc("get_event_summary", [event_id])
            # fetch all result sets from the call
            for result in cur.stored_results():
                rows = result.fetchall()
                st.dataframe(pd.DataFrame(rows))
            cur.close()
        except Error as e:
            st.error("Error calling stored procedure:")
            st.write(str(e))

# --- Sidebar + routing ---
menu = ["Login / Status", "Events", "Attendees", "Vendors", "Sponsors", "Event Summary"]
choice = st.sidebar.selectbox("Menu", menu)
st.sidebar.markdown("---")
if st.session_state.user_id:
    st.sidebar.write(f"Logged in as user_id = {st.session_state.user_id}")
    if st.sidebar.button("Logout"):
        logout()
else:
    st.sidebar.info("Not logged in")

# --- Page routing ---
try:
    if choice == "Login / Status":
        login_section()
    elif choice == "Events":
        manage_events()
    elif choice == "Attendees":
        manage_attendees()
    elif choice == "Vendors":
        manage_vendors()
    elif choice == "Sponsors":
        manage_sponsors()
    elif choice == "Event Summary":
        event_summary()
except Exception as e:
    st.error("An unexpected error occurred while rendering the page.")
    st.exception(e)
