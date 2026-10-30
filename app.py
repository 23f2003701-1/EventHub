import streamlit as st
import pandas as pd
import qrcode
import io
import random
import string
from datetime import datetime, date, timedelta

# ------------------------------------------------------------------
# PAGE CONFIG + GLOBAL STYLING
# ------------------------------------------------------------------
st.set_page_config(
    page_title="EventHub — Event Registration System",
    page_icon="🎟️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    /* ---------- THEME-AWARE VARIABLES ---------- */
    :root {
        --bg-card: #ffffff;
        --bg-sidebar: #f7f9fc;
        --border: #e6e9ef;
        --text-main: #1f2d3d;
        --text-muted: #5a6b7b;
        --accent: #2575fc;
        --shadow: 0 2px 8px rgba(0,0,0,0.06);
        --badge-open-bg: #e3f9e5;     --badge-open-fg: #1d7a33;
        --badge-full-bg: #fde8e8;     --badge-full-fg: #b42318;
        --badge-wait-bg: #fff4e5;     --badge-wait-fg: #b25e09;
        --badge-neutral-bg: #e8edf5;  --badge-neutral-fg: #34495e;
    }

    @media (prefers-color-scheme: dark) {
        :root {
            --bg-card: #1e2530;
            --bg-sidebar: #161b22;
            --border: #2d3748;
            --text-main: #e6edf3;
            --text-muted: #9aa7b8;
            --accent: #4b9bff;
            --shadow: 0 2px 10px rgba(0,0,0,0.45);
            --badge-open-bg: #163d24;     --badge-open-fg: #6ee7a3;
            --badge-full-bg: #4a1c1c;     --badge-full-fg: #ff9b9b;
            --badge-wait-bg: #4a3410;     --badge-wait-fg: #ffce7a;
            --badge-neutral-bg: #2a3442;  --badge-neutral-fg: #cbd5e1;
        }
    }

    .main .block-container { padding-top: 1.5rem; }
    h1, h2, h3, h4 { color: var(--text-main); }

    /* Hero banner */
    .hero {
        background: linear-gradient(135deg, #6a11cb 0%, #2575fc 100%);
        padding: 2rem 2.2rem;
        border-radius: 14px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        box-shadow: 0 6px 18px rgba(37,117,252,0.25);
    }
    .hero h1 { color: #ffffff !important; margin: 0; font-size: 2rem; }
    .hero p  { color: #e8eefc; margin: 0.3rem 0 0 0; }

    /* Metric cards */
    div[data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        padding: 14px 16px;
        border-radius: 12px;
        box-shadow: var(--shadow);
    }
    div[data-testid="stMetric"] label { color: var(--text-muted) !important; }
    div[data-testid="stMetricValue"]  { color: var(--text-main) !important; }

    /* Event cards */
    .event-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-left: 6px solid var(--accent);
        border-radius: 12px;
        padding: 16px 18px;
        margin-bottom: 14px;
        box-shadow: var(--shadow);
    }
    .event-card h4 { margin: 0 0 6px 0; color: var(--text-main); }
    .event-card .meta { color: var(--text-muted); font-size: 0.9rem; }

    /* Status badges */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        margin-left: 8px;
        vertical-align: middle;
        border: 1px solid transparent;
    }
    .badge-open     { background: var(--badge-open-bg);  color: var(--badge-open-fg); }
    .badge-full     { background: var(--badge-full-bg);  color: var(--badge-full-fg); }
    .badge-waitlist { background: var(--badge-wait-bg);  color: var(--badge-wait-fg); }
    .badge-paid     { background: var(--badge-open-bg);  color: var(--badge-open-fg); }
    .badge-pending  { background: var(--badge-wait-bg);  color: var(--badge-wait-fg); }
    .badge-refunded { background: var(--badge-neutral-bg); color: var(--badge-neutral-fg); }
    .badge-cancelled{ background: var(--badge-full-bg);  color: var(--badge-full-fg); }

    /* Sidebar — theme aware */
    section[data-testid="stSidebar"] {
        background: var(--bg-sidebar) !important;
        border-right: 1px solid var(--border);
    }
    section[data-testid="stSidebar"] * {
        color: var(--text-main) !important;
    }
    section[data-testid="stSidebar"] .stCaption,
    section[data-testid="stSidebar"] small {
        color: var(--text-muted) !important;
    }
    section[data-testid="stSidebar"] label p {
        color: var(--text-main) !important;
    }

    /* Containers (st.container(border=True)) */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--bg-card);
        border: 1px solid var(--border) !important;
        border-radius: 12px;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------
# CONSTANTS & DEMO USERS
# ------------------------------------------------------------------
DEMO_USERS = {
    "admin":      {"password": "admin123",   "role": "Admin",      "name": "Admin User"},
    "organizer":  {"password": "org123",     "role": "Organizer",  "name": "Olivia Organizer"},
    "attendee":   {"password": "attend123",  "role": "Attendee",   "name": "Aaron Attendee"},
    "attendee2":  {"password": "attend2123", "role": "Attendee",   "name": "Bella Attendee"},
}

CATEGORIES = ["Technology", "Music", "Sports", "Workshop", "Business", "Arts", "Health", "Other"]
PAYMENT_STATUSES = ["Pending", "Paid", "Refunded"]

# ------------------------------------------------------------------
# SESSION STATE INIT
# ------------------------------------------------------------------
def init_state():
    if "initialized" not in st.session_state:
        today = date.today()

        st.session_state.users = {u: dict(v) for u, v in DEMO_USERS.items()}

        st.session_state.events = [
            {
                "event_id": "EVT001",
                "title": "AI & Machine Learning Bootcamp",
                "category": "Technology",
                "description": "Hands-on introduction to ML pipelines and model deployment.",
                "date": str(today + timedelta(days=10)),
                "time": "10:00",
                "venue": "Innovation Hall, Block A",
                "capacity": 50,
                "fee": 499.0,
                "organizer": "organizer",
                "status": "Open",
                "created_at": str(datetime.now()),
            },
            {
                "event_id": "EVT002",
                "title": "Acoustic Night Live",
                "category": "Music",
                "description": "An evening of unplugged performances by local artists.",
                "date": str(today + timedelta(days=5)),
                "time": "18:30",
                "venue": "Open Air Amphitheatre",
                "capacity": 3,
                "fee": 250.0,
                "organizer": "organizer",
                "status": "Open",
                "created_at": str(datetime.now()),
            },
            {
                "event_id": "EVT003",
                "title": "Startup Pitch Workshop",
                "category": "Business",
                "description": "Craft and deliver a compelling investor pitch.",
                "date": str(today + timedelta(days=20)),
                "time": "14:00",
                "venue": "Seminar Room 204",
                "capacity": 30,
                "fee": 0.0,
                "organizer": "organizer",
                "status": "Open",
                "created_at": str(datetime.now()),
            },
        ]

        st.session_state.registrations = []
        st.session_state.reg_counter = 1000
        st.session_state.audit_log = []
        st.session_state.initialized = True

        log_action("SYSTEM", "Initialized demo data")


def log_action(user, action):
    st.session_state.audit_log.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user": user,
        "action": action,
    })


init_state()

# ------------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------------
def get_event(event_id):
    for e in st.session_state.events:
        if e["event_id"] == event_id:
            return e
    return None


def registered_count(event_id):
    return sum(
        1 for r in st.session_state.registrations
        if r["event_id"] == event_id and r["status"] == "Confirmed"
    )


def waitlist_count(event_id):
    return sum(
        1 for r in st.session_state.registrations
        if r["event_id"] == event_id and r["status"] == "Waitlisted"
    )


def seats_left(event):
    return event["capacity"] - registered_count(event["event_id"])


def update_event_status(event_id):
    e = get_event(event_id)
    if not e:
        return
    left = seats_left(e)
    if left <= 0:
        e["status"] = "Full"
    else:
        e["status"] = "Open"


def generate_ticket_id():
    st.session_state.reg_counter += 1
    return f"TKT-{st.session_state.reg_counter}"


def next_event_id():
    nums = [int(e["event_id"][3:]) for e in st.session_state.events if e["event_id"].startswith("EVT")]
    return f"EVT{max(nums) + 1:03d}" if nums else "EVT001"


def qr_bytes(data):
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def badge(text):
    cls = "badge-open"
    t = text.lower()
    if t in ("full", "cancelled"):
        cls = "badge-full"
    elif t in ("waitlisted", "pending"):
        cls = "badge-waitlist"
    elif t in ("confirmed", "paid", "open"):
        cls = "badge-open"
    elif t in ("refunded",):
        cls = "badge-refunded"
    return f'<span class="badge {cls}">{text}</span>'


def fmt_inr(x):
    return f"₹{x:,.0f}"


# ------------------------------------------------------------------
# AUTH
# ------------------------------------------------------------------
def login_screen():
    st.markdown("""
    <div class="hero">
        <h1>🎟️ EventHub</h1>
        <p>Event Registration & Management System — Streamlit Demo</p>
    </div>
    """, unsafe_allow_html=True)

    col_l, col_m, col_r = st.columns([1, 1.3, 1])
    with col_m:
        st.subheader("Sign in")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login", use_container_width=True)

        if submit:
            user = st.session_state.users.get(username.strip().lower())
            if not user:
                st.error("❌ User not found.")
                log_action(username, "Login failed — unknown user")
            elif user["password"] != password:
                st.error("❌ Incorrect password.")
                log_action(username, "Login failed — wrong password")
            else:
                st.session_state.logged_in = True
                st.session_state.username = username.strip().lower()
                st.session_state.role = user["role"]
                st.session_state.display_name = user["name"]
                log_action(st.session_state.username, f"Login success ({user['role']})")
                st.rerun()

        st.divider()
        st.caption("**Demo credentials**")
        cred_df = pd.DataFrame([
            {"Role": "Admin", "Username": "admin", "Password": "admin123"},
            {"Role": "Organizer", "Username": "organizer", "Password": "org123"},
            {"Role": "Attendee", "Username": "attendee", "Password": "attend123"},
            {"Role": "Attendee 2", "Username": "attendee2", "Password": "attend2123"},
        ])
        st.dataframe(cred_df, hide_index=True, use_container_width=True)


def logout():
    log_action(st.session_state.username, "Logout")
    for k in ["logged_in", "username", "role", "display_name"]:
        st.session_state.pop(k, None)
    st.rerun()


# ------------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------------
def sidebar():
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state.display_name}")
        st.caption(f"Role: **{st.session_state.role}**")
        st.divider()

        role = st.session_state.role
        pages = ["🏠 Home", "📅 Browse Events"]
        if role in ("Organizer", "Admin"):
            pages += ["➕ Create Event", "🗂️ Manage Events"]
        if role == "Attendee":
            pages += ["🎟️ My Registrations"]
        if role in ("Organizer", "Admin"):
            pages += ["📊 Reports"]
        if role == "Admin":
            pages += ["🛡️ Admin Panel", "📜 Audit Log"]

        page = st.radio("Navigation", pages, label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            logout()
    return page


# ------------------------------------------------------------------
# PAGE: HOME
# ------------------------------------------------------------------
def page_home():
    st.markdown(f"""
    <div class="hero">
        <h1>Welcome back, {st.session_state.display_name.split()[0]} 👋</h1>
        <p>Here's a snapshot of what's happening in EventHub.</p>
    </div>
    """, unsafe_allow_html=True)

    total_events = len(st.session_state.events)
    open_events = sum(1 for e in st.session_state.events if e["status"] == "Open")
    total_regs = sum(1 for r in st.session_state.registrations if r["status"] == "Confirmed")
    waitlisted = sum(1 for r in st.session_state.registrations if r["status"] == "Waitlisted")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Events", total_events)
    c2.metric("Open Events", open_events)
    c3.metric("Confirmed Registrations", total_regs)
    c4.metric("Waitlisted", waitlisted)

    st.divider()
    st.subheader("Upcoming Events")
    upcoming = sorted(
        [e for e in st.session_state.events if e["date"] >= str(date.today())],
        key=lambda x: x["date"],
    )[:4]

    if not upcoming:
        st.info("No upcoming events yet.")
        return

    for e in upcoming:
        left = seats_left(e)
        st.markdown(f"""
        <div class="event-card">
            <h4>{e['title']} {badge(e['status'])}</h4>
            <div class="meta">
                📅 {e['date']} &nbsp;·&nbsp; 🕐 {e['time']} &nbsp;·&nbsp; 📍 {e['venue']}<br>
                🏷️ {e['category']} &nbsp;·&nbsp; 💰 {fmt_inr(e['fee']) if e['fee'] > 0 else 'Free'} &nbsp;·&nbsp;
                🪑 {left} / {e['capacity']} seats left
            </div>
        </div>
        """, unsafe_allow_html=True)


# ------------------------------------------------------------------
# PAGE: BROWSE EVENTS
# ------------------------------------------------------------------
def page_browse():
    st.markdown("## 📅 Browse Events")
    st.caption("Discover and register for upcoming events.")

    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search = st.text_input("🔍 Search by title or venue", "")
    with f2:
        cat_filter = st.selectbox("Category", ["All"] + CATEGORIES)
    with f3:
        status_filter = st.selectbox("Status", ["All", "Open", "Full"])

    events = st.session_state.events
    if search:
        events = [e for e in events if search.lower() in e["title"].lower() or search.lower() in e["venue"].lower()]
    if cat_filter != "All":
        events = [e for e in events if e["category"] == cat_filter]
    if status_filter != "All":
        events = [e for e in events if e["status"] == status_filter]

    events = sorted(events, key=lambda x: x["date"])

    if not events:
        st.warning("No events match your filters.")
        return

    for e in events:
        left = seats_left(e)
        wl = waitlist_count(e["event_id"])
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f'<h3 style="margin-bottom:4px;">{e["title"]} {badge(e["status"])}</h3>',
                    unsafe_allow_html=True,
                )
                st.caption(f"📅 {e['date']} · 🕐 {e['time']} · 📍 {e['venue']}")
                st.write(e["description"])
                st.caption(
                    f"🏷️ {e['category']} · 💰 {fmt_inr(e['fee']) if e['fee'] > 0 else 'Free'} · "
                    f"🪑 {left} seats left · ⏳ {wl} on waitlist"
                )
            with c2:
                if st.session_state.role != "Attendee":
                    st.info("Attendee role required to register.")
                elif e["status"] == "Full":
                    if st.button("Join Waitlist", key=f"wl_{e['event_id']}", use_container_width=True):
                        register_for_event(e, waitlist=True)
                else:
                    if st.button("Register", key=f"reg_{e['event_id']}", use_container_width=True, type="primary"):
                        register_for_event(e, waitlist=False)


def register_for_event(event, waitlist=False):
    username = st.session_state.username

    existing = next(
        (r for r in st.session_state.registrations
         if r["event_id"] == event["event_id"] and r["username"] == username
         and r["status"] in ("Confirmed", "Waitlisted")),
        None,
    )
    if existing:
        st.error(f"❌ You already have a {existing['status'].lower()} registration for this event.")
        return

    if event["date"] < str(date.today()):
        st.error("❌ Cannot register for a past event.")
        return

    left = seats_left(event)
    if not waitlist and left <= 0:
        st.error("❌ Event is full. Please join the waitlist.")
        return

    status = "Waitlisted" if waitlist else "Confirmed"
    reg = {
        "ticket_id": generate_ticket_id(),
        "event_id": event["event_id"],
        "event_title": event["title"],
        "username": username,
        "name": st.session_state.display_name,
        "registered_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "payment_status": "Pending" if event["fee"] > 0 else "Paid",
        "fee": event["fee"],
    }
    st.session_state.registrations.append(reg)

    update_event_status(event["event_id"])
    log_action(username, f"{'Waitlisted for' if waitlist else 'Registered for'} {event['event_id']}")

    if waitlist:
        st.success(f"⏳ Added to waitlist for **{event['title']}**. Ticket: {reg['ticket_id']}")
    else:
        st.success(f"✅ Registered for **{event['title']}**! Ticket: {reg['ticket_id']}")
    st.rerun()


# ------------------------------------------------------------------
# PAGE: CREATE EVENT
# ------------------------------------------------------------------
def page_create_event():
    st.markdown("## ➕ Create New Event")

    with st.form("create_event_form"):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("Event Title *")
            category = st.selectbox("Category *", CATEGORIES)
            event_date = st.date_input("Event Date *", min_value=date.today())
            event_time = st.time_input("Event Time *")
        with c2:
            venue = st.text_input("Venue *")
            capacity = st.number_input("Capacity *", min_value=1, max_value=10000, value=50)
            fee = st.number_input("Fee (₹) *", min_value=0.0, value=0.0, step=50.0)

        description = st.text_area("Description *", height=100)

        submitted = st.form_submit_button("Create Event", type="primary", use_container_width=True)

    if submitted:
        errors = []
        if not title.strip():
            errors.append("Title is required.")
        if len(title.strip()) > 100:
            errors.append("Title must be ≤ 100 characters.")
        if not venue.strip():
            errors.append("Venue is required.")
        if not description.strip():
            errors.append("Description is required.")
        if event_date < date.today():
            errors.append("Event date cannot be in the past.")
        if capacity < 1:
            errors.append("Capacity must be at least 1.")

        if errors:
            for err in errors:
                st.error(f"❌ {err}")
            return

        eid = next_event_id()
        new_event = {
            "event_id": eid,
            "title": title.strip(),
            "category": category,
            "description": description.strip(),
            "date": str(event_date),
            "time": event_time.strftime("%H:%M"),
            "venue": venue.strip(),
            "capacity": int(capacity),
            "fee": float(fee),
            "organizer": st.session_state.username,
            "status": "Open",
            "created_at": str(datetime.now()),
        }
        st.session_state.events.append(new_event)
        log_action(st.session_state.username, f"Created event {eid}")
        st.success(f"✅ Event **{title}** created successfully (ID: {eid}).")
        st.rerun()


# ------------------------------------------------------------------
# PAGE: MANAGE EVENTS
# ------------------------------------------------------------------
def page_manage_events():
    st.markdown("## 🗂️ Manage Events")

    owned = [
        e for e in st.session_state.events
        if st.session_state.role == "Admin" or e["organizer"] == st.session_state.username
    ]

    if not owned:
        st.info("You haven't created any events yet.")
        return

    for e in owned:
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f'<h3 style="margin-bottom:4px;">{e["title"]} {badge(e["status"])}</h3>',
                    unsafe_allow_html=True,
                )
                st.caption(
                    f"📅 {e['date']} · 🕐 {e['time']} · 📍 {e['venue']} · "
                    f"🪑 {registered_count(e['event_id'])}/{e['capacity']} registered · "
                    f"⏳ {waitlist_count(e['event_id'])} waitlisted"
                )
            with c2:
                new_cap = st.number_input(
                    "Capacity", min_value=1,
                    value=int(e["capacity"]),
                    key=f"cap_{e['event_id']}",
                    label_visibility="collapsed",
                )
                if new_cap != e["capacity"]:
                    if new_cap >= registered_count(e["event_id"]):
                        e["capacity"] = int(new_cap)
                        update_event_status(e["event_id"])
                        log_action(st.session_state.username, f"Updated capacity for {e['event_id']}")
                        st.rerun()
                    else:
                        st.warning("Capacity cannot be less than current registrations.")

                if st.button("🗑️ Delete Event", key=f"del_{e['event_id']}", use_container_width=True):
                    st.session_state.events = [x for x in st.session_state.events if x["event_id"] != e["event_id"]]
                    st.session_state.registrations = [
                        r for r in st.session_state.registrations if r["event_id"] != e["event_id"]
                    ]
                    log_action(st.session_state.username, f"Deleted event {e['event_id']}")
                    st.success("Event deleted.")
                    st.rerun()


# ------------------------------------------------------------------
# PAGE: MY REGISTRATIONS
# ------------------------------------------------------------------
def page_my_registrations():
    st.markdown("## 🎟️ My Registrations")

    mine = [
        r for r in st.session_state.registrations
        if r["username"] == st.session_state.username
    ]

    if not mine:
        st.info("You have no registrations yet. Browse events to get started!")
        return

    for r in sorted(mine, key=lambda x: x["registered_at"], reverse=True):
        with st.container(border=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"### {r['event_title']}")
                st.markdown(f"{badge(r['status'])} {badge(r['payment_status'])}", unsafe_allow_html=True)
                st.caption(
                    f"🎫 Ticket: **{r['ticket_id']}** · "
                    f"📅 Registered: {r['registered_at']} · "
                    f"💰 Fee: {fmt_inr(r['fee']) if r['fee'] > 0 else 'Free'}"
                )
            with c2:
                qr_data = f"{r['ticket_id']}|{r['event_id']}|{r['username']}"
                st.image(qr_bytes(qr_data), caption="Ticket QR", width=110)

                if r["status"] == "Confirmed":
                    if r["payment_status"] == "Pending" and r["fee"] > 0:
                        if st.button("💳 Pay Now", key=f"pay_{r['ticket_id']}", use_container_width=True):
                            r["payment_status"] = "Paid"
                            log_action(st.session_state.username, f"Paid for {r['ticket_id']}")
                            st.rerun()

                    if st.button("❌ Cancel", key=f"cancel_{r['ticket_id']}", use_container_width=True):
                        cancel_registration(r)

                elif r["status"] == "Waitlisted":
                    if st.button("🚫 Leave Waitlist", key=f"leave_{r['ticket_id']}", use_container_width=True):
                        cancel_registration(r)


def cancel_registration(reg):
    event = get_event(reg["event_id"])
    was_confirmed = reg["status"] == "Confirmed"

    reg["status"] = "Cancelled"
    if reg["payment_status"] == "Paid":
        reg["payment_status"] = "Refunded"

    if was_confirmed and event:
        waitlist = sorted(
            [x for x in st.session_state.registrations
             if x["event_id"] == reg["event_id"] and x["status"] == "Waitlisted"],
            key=lambda x: x["registered_at"],
        )
        if waitlist:
            promoted = waitlist[0]
            promoted["status"] = "Confirmed"
            log_action("SYSTEM", f"Promoted {promoted['ticket_id']} from waitlist")
            st.info(f"ℹ️ {promoted['name']} was promoted from the waitlist.")

    if event:
        update_event_status(event["event_id"])
    log_action(st.session_state.username, f"Cancelled {reg['ticket_id']}")
    st.success("Registration cancelled.")
    st.rerun()


# ------------------------------------------------------------------
# PAGE: REPORTS
# ------------------------------------------------------------------
def page_reports():
    st.markdown("## 📊 Reports & Analytics")

    regs = st.session_state.registrations
    events = st.session_state.events

    total_regs = sum(1 for r in regs if r["status"] == "Confirmed")
    total_cancelled = sum(1 for r in regs if r["status"] == "Cancelled")
    total_waitlisted = sum(1 for r in regs if r["status"] == "Waitlisted")
    revenue = sum(r["fee"] for r in regs if r["payment_status"] == "Paid")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Confirmed", total_regs)
    c2.metric("Waitlisted", total_waitlisted)
    c3.metric("Cancelled", total_cancelled)
    c4.metric("Revenue", fmt_inr(revenue))

    st.divider()

    st.subheader("Registrations by Event")
    rows = []
    for e in events:
        confirmed = registered_count(e["event_id"])
        wl = waitlist_count(e["event_id"])
        rev = sum(
            r["fee"] for r in regs
            if r["event_id"] == e["event_id"] and r["payment_status"] == "Paid"
        )
        rows.append({
            "Event ID": e["event_id"],
            "Title": e["title"],
            "Capacity": e["capacity"],
            "Confirmed": confirmed,
            "Waitlisted": wl,
            "Seats Left": seats_left(e),
            "Fill %": f"{(confirmed / e['capacity'] * 100):.1f}%" if e["capacity"] else "0%",
            "Revenue": fmt_inr(rev),
        })
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)

    st.divider()

    st.subheader("Category Breakdown")
    cat_rows = []
    for cat in CATEGORIES:
        cat_events = [e for e in events if e["category"] == cat]
        cat_regs = sum(registered_count(e["event_id"]) for e in cat_events)
        if cat_events:
            cat_rows.append({"Category": cat, "Events": len(cat_events), "Confirmed Registrations": cat_regs})
    if cat_rows:
        st.dataframe(pd.DataFrame(cat_rows), hide_index=True, use_container_width=True)

    st.divider()

    st.subheader("Export Data")
    if regs:
        df = pd.DataFrame(regs)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download Registrations CSV",
            data=csv,
            file_name=f"registrations_{date.today()}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    else:
        st.caption("No registration data to export.")


# ------------------------------------------------------------------
# PAGE: ADMIN PANEL
# ------------------------------------------------------------------
def page_admin():
    st.markdown("## 🛡️ Admin Panel")
    st.caption("Admin-only controls: user management and system overrides.")

    tab1, tab2 = st.tabs(["👥 Users", "📋 All Registrations"])

    with tab1:
        st.subheader("Registered Users")
        rows = [
            {"Username": u, "Name": v["name"], "Role": v["role"]}
            for u, v in st.session_state.users.items()
        ]
        st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
        st.caption("This is a demo; user creation is disabled.")

    with tab2:
        st.subheader("All Registrations (system-wide)")
        regs = st.session_state.registrations
        if not regs:
            st.info("No registrations yet.")
        else:
            df = pd.DataFrame(regs)
            st.dataframe(
                df[["ticket_id", "event_title", "name", "status", "payment_status", "registered_at"]],
                hide_index=True,
                use_container_width=True,
            )

            st.divider()
            st.subheader("Override Payment Status")
            tkt = st.selectbox("Select Ticket", [r["ticket_id"] for r in regs])
            new_status = st.selectbox("New Payment Status", PAYMENT_STATUSES)
            if st.button("Update Payment Status", type="primary"):
                for r in regs:
                    if r["ticket_id"] == tkt:
                        r["payment_status"] = new_status
                        log_action(st.session_state.username, f"Override payment {tkt} → {new_status}")
                        st.success(f"Updated {tkt} → {new_status}")
                        st.rerun()


# ------------------------------------------------------------------
# PAGE: AUDIT LOG
# ------------------------------------------------------------------
def page_audit():
    st.markdown("## 📜 Audit Log")
    st.caption("Every login, registration, cancellation, and admin action is recorded here.")

    logs = st.session_state.audit_log
    if not logs:
        st.info("No audit entries yet.")
        return

    df = pd.DataFrame(logs[::-1])
    st.dataframe(df, hide_index=True, use_container_width=True)

    st.divider()
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Audit Log CSV",
        data=csv,
        file_name=f"audit_log_{date.today()}.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------------
# ROUTER
# ------------------------------------------------------------------
def main():
    if not st.session_state.get("logged_in"):
        login_screen()
        return

    page = sidebar()

    if page == "🏠 Home":
        page_home()
    elif page == "📅 Browse Events":
        page_browse()
    elif page == "➕ Create Event":
        page_create_event()
    elif page == "🗂️ Manage Events":
        page_manage_events()
    elif page == "🎟️ My Registrations":
        page_my_registrations()
    elif page == "📊 Reports":
        page_reports()
    elif page == "🛡️ Admin Panel":
        page_admin()
    elif page == "📜 Audit Log":
        page_audit()


if __name__ == "__main__":
    main()