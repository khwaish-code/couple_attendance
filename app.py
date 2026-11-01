
import streamlit as st
from supabase import create_client, Client
from datetime import date, datetime, timedelta
import calendar

# ---------------- CONFIGURATION ----------------

st.set_page_config(
    page_title="Our Love Attendance ❤️",
    page_icon="💕",
    layout="centered"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #fff0f5, #ffe4ec);
}
h1, h2, h3 {
    color: #d63384;
    text-align: center;
}
div.stButton > button {
    background-color: #ff69a4;
    color: white;
    border-radius: 20px;
    border: none;
}
</style>
""", unsafe_allow_html=True)

st.title("💕 Our Little Love Attendance 💕")
st.caption("Two hearts, one attendance diary ❤️")

# Set these in Streamlit Secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- AUTHENTICATION ----------------

if "user" not in st.session_state:
    st.session_state.user = None

if "couple_id" not in st.session_state:
    st.session_state.couple_id = None

if not st.session_state.user:
    st.subheader("Welcome, lovebirds 💗")

    tab1, tab2 = st.tabs(["Login", "Create account"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login ❤️"):
            try:
                result = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.user = result.user
                st.rerun()
            except Exception as e:
                st.error("Login failed. Check your email and password.")

    with tab2:
        email = st.text_input("Your email", key="signup_email")
        password = st.text_input("Create password", type="password", key="signup_password")

        if st.button("Create account 💕"):
            try:
                result = supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                st.success("Account created! If email confirmation is enabled, verify your email before logging in.")
            except Exception:
                st.error("Could not create account. Please check your details.")

    st.stop()

# ---------------- COUPLE SETUP ----------------

user_id = st.session_state.user.id

try:
    profile = (
        supabase.table("profiles")
        .select("couple_id, display_name")
        .eq("id", user_id)
        .maybe_single()
        .execute()
    ).data
except Exception:
    profile = None

if not profile or not profile.get("couple_id"):
    st.subheader("Connect your couple account 💞")
    st.write("Create a shared space, or join your partner's space using their invite code.")

    name = st.text_input("Your display name")

    if st.button("Create our space 💗"):
        try:
            result = supabase.rpc("create_couple", {
                "p_display_name": name
            }).execute()
            st.success("Your shared space is ready! Refresh the page.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not create space: {e}")

    invite_code = st.text_input("Partner's invite code")

    if st.button("Join partner's space 💌"):
        try:
            supabase.rpc("join_couple", {
                "p_invite_code": invite_code,
                "p_display_name": name
            }).execute()
            st.success("You joined your partner's space!")
            st.rerun()
        except Exception as e:
            st.error(f"Could not join: {e}")

    st.stop()

couple_id = profile["couple_id"]
st.session_state.couple_id = couple_id

# ---------------- ATTENDANCE ----------------

members = (
    supabase.table("profiles")
    .select("id, display_name")
    .eq("couple_id", couple_id)
    .execute()
).data or []

my_name = next(
    (m["display_name"] for m in members if m["id"] == user_id),
    "Me"
)

partner = next((m for m in members if m["id"] != user_id), None)

st.markdown(f"### Hello, {my_name} 💖")

if partner:
    st.caption(f"Your attendance partner: {partner['display_name']}")

# Fetch records
records = (
    supabase.table("attendance")
    .select("*")
    .eq("couple_id", couple_id)
    .order("attendance_date")
    .execute()
).data or []

# Date selection allows backdated entries
selected_date = st.date_input(
    "Choose attendance date",
    value=date.today(),
    min_value=date.today() - timedelta(days=365)
)

date_string = selected_date.isoformat()

existing = next(
    (r for r in records if r["attendance_date"] == date_string),
    None
)

st.subheader("Our daily check-in 🌷")

if existing:
    st.info("Attendance has already been recorded for this date.")
    st.write(f"You: {'Available' if existing.get('user1_available') else 'Unavailable'}")
    st.write(f"Partner: {'Available' if existing.get('user2_available') else 'Unavailable'}")
else:
    my_available = st.radio(
        "Were you available?",
        ["Yes 💗", "No 🌙"],
        horizontal=True
    )

    partner_available = st.radio(
        "Was your partner available?",
        ["Yes 💗", "No 🌙"],
        horizontal=True
    )

    if st.button("Save our attendance 💕"):
        is_me_available = my_available.startswith("Yes")
        is_partner_available = partner_available.startswith("Yes")

        if not is_me_available and not is_partner_available:
            status = "holiday"
        else:
            status = "present"

        try:
            supabase.table("attendance").insert({
                "couple_id": couple_id,
                "attendance_date": date_string,
                "user1_available": is_me_available,
                "user2_available": is_partner_available,
                "status": status
            }).execute()
            st.success("Attendance saved! ❤️")
            st.rerun()
        except Exception as e:
            st.error(f"Could not save attendance: {e}")

# ---------------- MONTHLY SUMMARY ----------------

st.divider()
st.subheader("Our monthly love report 💞")

today = date.today()
selected_month = st.selectbox(
    "Choose month",
    list(range(1, 13)),
    index=today.month - 1,
    format_func=lambda m: calendar.month_name[m]
)

selected_year = st.number_input(
    "Year",
    min_value=2020,
    max_value=2100,
    value=today.year
)

month_records = [
    r for r in records
    if datetime.strptime(r["attendance_date"], "%Y-%m-%d").year == selected_year
    and datetime.strptime(r["attendance_date"], "%Y-%m-%d").month == selected_month
]

working_days = [r for r in month_records if r["status"] != "holiday"]
holidays = len(month_records) - len(working_days)

if working_days:
    both_present = sum(
        1 for r in working_days
        if r.get("user1_available") and r.get("user2_available")
    )
    my_present = sum(1 for r in working_days if r.get("user1_available"))
    partner_present = sum(1 for r in working_days if r.get("user2_available"))

    st.metric("Both present", f"{both_present / len(working_days) * 100:.1f}%")
    st.metric("My attendance", f"{my_present / len(working_days) * 100:.1f}%")
    st.metric("Partner attendance", f"{partner_present / len(working_days) * 100:.1f}%")
    st.metric("Shared holidays", holidays)
else:
    st.info("No attendance recorded for this month yet.")

# ---------------- CALENDAR ----------------

st.divider()
st.subheader("Our calendar 📅")

cal = calendar.monthcalendar(int(selected_year), selected_month)

for week in cal:
    cols = st.columns(7)
    for i, day in enumerate(week):
        if day == 0:
            cols[i].write(" ")
            continue

        record = next(
            (r for r in month_records if r["attendance_date"] == date(
                int(selected_year), selected_month, day
            ).isoformat()),
            None
        )

        if record:
            if record["status"] == "holiday":
                symbol = "🌴"
            elif record.get("user1_available") and record.get("user2_available"):
                symbol = "💗"
            elif record.get("user1_available") or record.get("user2_available"):
                symbol = "💛"
            else:
                symbol = "❌"
        else:
            symbol = "·"

        cols[i].markdown(f"**{day}**<br>{symbol}", unsafe_allow_html=True)

# ---------------- LOGOUT ----------------

st.divider()

if st.button("Logout 💌"):
    supabase.auth.sign_out()
    st.session_state.user = None
    st.session_state.couple_id = None
    st.rerun()
