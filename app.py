# app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from functions import (
    add_expense, get_expenses_df, update_expense, delete_expense,
    UPLOAD_DIR, geocode_location
)
from datetime import datetime
import os
from PIL import Image
import base64

st.set_page_config(page_title="WanderLog — Journey Timeline", layout="wide", page_icon="🧭")

# ---------- Style / Theme ----------
page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(135deg, #0f1724, #071124, #05253b);
    color: #e6f2ff;
}
[data-testid="stSidebar"] {
    background-color: rgba(4, 8, 15, 0.6);
}
.card {
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 12px;
}
.trip-title {
    font-weight:700;
    color:#7ee7ff;
}
.small-muted {
    color: #b8d6e6;
    font-size:12px;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

# ---------- Header ----------
st.markdown("<h1 style='text-align:center;color:#7EE7FF;'>WanderLog — A Visual Journey of Expenses & Memories</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center;color:#cfeef9;'>Turn your travel spends into a cinematic timeline — map pins, photos, emojis, and story notes.</p>", unsafe_allow_html=True)
st.markdown("---")

# ---------- Sidebar ----------
menu = ["Add Expense", "View Expenses", "Journey Timeline", "Analytics", "Settings"]
choice = st.sidebar.selectbox("Menu", menu, index=2)
st.sidebar.markdown("Made with ❤️ by Rizwana")
st.sidebar.markdown("Pro tip: add a photo and an emoji to make trips pop on the timeline.")

# ---------- Utilities ----------
def img_to_bytes(img_path):
    try:
        with open(img_path, "rb") as f:
            data = f.read()
            return base64.b64encode(data).decode()
    except Exception:
        return None

# ---------- PAGE: Add Expense ----------
if choice == "Add Expense":
    st.subheader("Add a New Travel Expense (with memory)")
    with st.form("add_form", clear_on_submit=True):
        date = st.date_input("Date")
        trip_name = st.text_input("Trip name (e.g., 'Mumbai Conference', 'Kerala Trip')")
        category = st.selectbox("Category", ["Flight", "Hotel", "Food", "Transport", "Sightseeing", "Other"])
        amount = st.number_input("Amount (INR)", min_value=0.0, step=1.0)
        location = st.text_input("Location (City, Country or landmark)")
        emoji = st.text_input("Emoji (single emoji e.g. ✨ 🍛 🏨) — optional", max_chars=4)
        description = st.text_area("Short memory/description (optional)")
        uploaded_file = st.file_uploader("Attach a photo memory (optional)", type=["png","jpg","jpeg","webp"])
        submitted = st.form_submit_button("Save Memory & Expense")

        submitted = st.form_submit_button("Add Expense")

    if submitted:
        errors = []

        # ---- Validation checks ----
        if category == "Select":
            errors.append("⚠️ Please select a category.")
        try:
            amount_val = float(amount)
            if amount_val <= 0:
                errors.append("⚠️ Amount must be greater than 0.")
        except ValueError:
            errors.append("⚠️ Amount must be a valid number.")

        if not location.strip():
            errors.append("⚠️ Location cannot be empty.")
        if len(description.strip()) < 3:
            errors.append("⚠️ Description must have at least 3 characters.")
        if emoji and not any(ch in emoji for ch in "😀😃😄😁😆😅😂🤣😊😇🙂🙃😉😌😍🥰😘😗😙😚😋😛😝😜🤪🤨🧐🤓😎🤩🥳🤗🤔"):
            errors.append("⚠️ Emoji must contain at least one valid emoji symbol.")

        if errors:
            for e in errors:
                st.warning(e)
        else:
            # ✅ Save to DB
            add_expense(date, category, amount_val, location, description, emoji)
            st.success("✅ Expense added successfully!")

# ---------- PAGE: View Expenses ----------
elif choice == "View Expenses":
    st.subheader("All Expenses — Table & Quick Actions")
    df = get_expenses_df()
    if df.empty:
        st.info("No expenses yet. Add one in the Add Expense section.")
    else:
        df_display = df.copy()
        df_display['date'] = pd.to_datetime(df_display['date']).dt.date
        st.dataframe(df_display[['id','date','trip_name','location','category','amount','emoji']].sort_values('date', ascending=False), height=400)

        st.markdown("### Edit or Delete an Entry")
        cols = st.columns([1,1,1])
        with cols[0]:
            selected_id = st.number_input("Enter ID to edit/delete", min_value=int(df['id'].min()), max_value=int(df['id'].max()), step=1, value=int(df['id'].max()))
        with cols[1]:
            if st.button("Load Entry"):
                st.session_state['edit_id'] = selected_id
        with cols[2]:
            if st.button("Refresh"):
                st.experimental_rerun()

        if 'edit_id' in st.session_state:
            entry = df[df['id']==st.session_state['edit_id']]
            if not entry.empty:
                entry = entry.iloc[0]
                st.markdown(f"#### Editing ID {entry['id']} — {entry.get('trip_name','')}")
                with st.form("edit_form"):
                    date = st.date_input("Date", value=pd.to_datetime(entry['date']).date())
                    trip_name = st.text_input("Trip name", value=entry.get('trip_name','') or "")
                    category = st.selectbox("Category", ["Flight","Hotel","Food","Transport","Sightseeing","Other"], index=["Flight","Hotel","Food","Transport","Sightseeing","Other"].index(entry['category']) if entry['category'] in ["Flight","Hotel","Food","Transport","Sightseeing","Other"] else 5)
                    amount = st.number_input("Amount", value=float(entry['amount']))
                    location = st.text_input("Location", value=entry.get('location','') or "")
                    emoji = st.text_input("Emoji", value=entry.get('emoji','') or "", max_chars=4)
                    st.markdown(f"<h3 style='font-size:40px'>{emoji}</h3>", unsafe_allow_html=True)

                    description = st.text_area("Description", value=entry.get('description','') or "")
                    keep_photo = entry.get('photo_path', None)
                    st.markdown("Current Photo:")
                    if keep_photo and os.path.exists(keep_photo):
                        st.image(keep_photo, width=240)
                    else:
                        st.markdown("_No photo attached_")
                    new_photo = st.file_uploader("Replace photo (optional)", type=["png","jpg","jpeg","webp"])
                    update_btn = st.form_submit_button("Update")
                    delete_btn = st.form_submit_button("Delete This Entry")
                    if update_btn:
                        update_expense(entry['id'], date, trip_name, category, amount, description, location, emoji, keep_photo, new_photo)
                        st.success("Updated successfully.")
                        st.experimental_rerun()
                    if delete_btn:
                        delete_expense(entry['id'])
                        st.success("Deleted entry.")
                        st.experimental_rerun()
            else:
                st.warning("Entry not found. Please refresh or check ID.")

# ---------- PAGE: Journey Timeline ----------
elif choice == "Journey Timeline":
    st.subheader("Journey Timeline — Relive your trips")
    df = get_expenses_df()
    if df.empty:
        st.info("No trips yet. Add expenses with photos to see your Journey.")
    else:
        # prepare timeline dataframe: group by trip_name (if present) or location+month grouping
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        # create an event label with emoji and category
        df['label'] = df.apply(lambda r: f"{r.get('emoji','') or ''} {r.get('trip_name') or r.get('location','')} — ₹{r['amount']:.0f}", axis=1)
        # timeline plot
        timeline = go.Figure()

        timeline.add_trace(go.Scatter(
            x=df['date'],
            y=[1]*len(df),
            mode='markers+text',
            marker=dict(size=18, color='rgba(126,231,255,0.9)', line=dict(width=2, color='white')),
            text=df['label'],
            textposition="top center",
            hovertemplate="<b>%{text}</b><br>Date: %{x|%Y-%m-%d}<br>Category: %{customdata[0]}<br>Location: %{customdata[1]}<extra></extra>",
            customdata=df[['category','location']].values
        ))

        timeline.update_layout(
            showlegend=False,
            height=300,
            xaxis=dict(title="Trip Timeline", showgrid=True),
            yaxis=dict(visible=False),
            margin=dict(l=40, r=40, t=30, b=30),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(timeline, use_container_width=True)

        st.markdown("---")
        st.markdown("#### Trip Gallery")
        # gallery of entries in chronological order
        cols = st.columns(3)
        for idx, row in df.iterrows():
            c = cols[idx % 3]
            with c:
                card = st.container()
                with card:
                    title = f"{row.get('emoji','')} {row.get('trip_name') or row.get('location','')}"
                    st.markdown(f"<div class='trip-title'>{title}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='small-muted'>{row['date'].date()} · ₹{row['amount']:.2f} · {row['category']}</div>", unsafe_allow_html=True)
                    if row.get('photo_path') and os.path.exists(row['photo_path']):
                        st.image(row['photo_path'], use_column_width=True, caption=row.get('description',''), output_format='auto')
                    else:
                        # placeholder
                        st.write("📍 " + (row.get('location') or "Unknown location"))
                        st.markdown(f"_{row.get('description','') or 'No description'}_")
                    if st.button(f"Center on Map — ID {row['id']}", key=f"map_{row['id']}"):
                        # store center info in session to be used below
                        st.session_state['center_lat'] = float(row['latitude']) if row['latitude'] else None
                        st.session_state['center_lon'] = float(row['longitude']) if row['longitude'] else None
                        st.session_state['center_zoom'] = 6

        # Map below
        st.markdown("---")
        st.markdown("### Map — Your Memories Around the World")
        map_df = df.dropna(subset=['latitude','longitude'])
        if map_df.empty:
            st.info("Map will appear once you add at least one expense with a valid location.")
        else:
            # default center: mean coords
            if 'center_lat' in st.session_state and st.session_state.get('center_lat'):
                center = {"lat": st.session_state['center_lat'], "lon": st.session_state['center_lon']}
                zoom = st.session_state.get('center_zoom', 2)
            else:
                center = {"lat": map_df['latitude'].mean(), "lon": map_df['longitude'].mean()}
                zoom = 2

            map_fig = px.scatter_mapbox(map_df,
                                        lat="latitude", lon="longitude",
                                        size="amount",
                                        color="category",
                                        hover_name="label",
                                        hover_data=["date","amount","description"],
                                        zoom=zoom,
                                        height=500)
            map_fig.update_layout(mapbox_style="open-street-map",
                                  mapbox_center=center,
                                  margin={"r":0,"t":0,"l":0,"b":0})
            st.plotly_chart(map_fig, use_container_width=True)

# ---------- PAGE: Analytics ----------
elif choice == "Analytics":
    st.subheader("Cinematic Analytics — Insights & Top Stories")
    df = get_expenses_df()
    if df.empty:
        st.info("No data yet. Add expenses to view insights.")
    else:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime("%b %Y")
        total = df['amount'].sum()
        avg = df['amount'].mean()
        top_loc = df.groupby('location')['amount'].sum().idxmax() if not df['location'].isna().all() else "N/A"
        top_cat = df.groupby('category')['amount'].sum().idxmax()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Spent", f"₹{total:,.2f}")
        c2.metric("Avg Expense", f"₹{avg:,.2f}")
        c3.metric("Top Location", top_loc)
        c4.metric("Top Category", top_cat)

        st.markdown("---")
        # category donut
        cat_df = df.groupby('category')['amount'].sum().reset_index()
        fig = px.pie(cat_df, names='category', values='amount', hole=0.45, title="Spending by Category")
        fig.update_traces(textinfo='percent+label')
        st.plotly_chart(fig, use_container_width=True)

        # monthly bar
        monthly = df.groupby('month')['amount'].sum().reset_index()
        monthly = monthly.sort_values('month')
        bar = px.bar(monthly, x='month', y='amount', title="Monthly Spend", labels={'amount':'Amount (₹)'})
        st.plotly_chart(bar, use_container_width=True)

        # top 5 locations
        loc_sum = df.groupby('location')['amount'].sum().reset_index().sort_values('amount', ascending=False).head(8)
        if not loc_sum.empty:
            bar2 = px.bar(loc_sum, x='location', y='amount', title="Top Spending Locations")
            st.plotly_chart(bar2, use_container_width=True)

# ---------- PAGE: Settings ----------
elif choice == "Settings":
    st.subheader("Settings & Maintenance")
    st.markdown("**Uploads folder path:** `" + os.path.abspath(UPLOAD_DIR) + "`")
    if st.button("Clear All Session State"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        st.success("Session state cleared.")
    st.markdown("**Note:** Photos are stored in the uploads folder. Deleting DB entries will also attempt to remove photos.")

