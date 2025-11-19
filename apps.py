import streamlit as st
import pandas as pd
import plotly.express as px

page_bg = """
<style>
[data-testid="stAppViewContainer"] {
    background-image: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}
[data-testid="stSidebar"] {
    background-color: rgba(20, 30, 40, 0.95);
}
h1, h2, h3, h4, h5, h6 {
    color: #00BFFF;
}
</style>
"""
st.markdown(page_bg, unsafe_allow_html=True)

from functions import add_expense, get_expenses, update_expense, delete_expense

st.set_page_config(page_title="Travel Expense Tracker", layout="wide")
st.title("✈️ Travel Expense Tracker")

menu = ["Add Expense", "View Expenses", "Edit/Delete Expense", "Analytics"]
choice = st.sidebar.selectbox("Menu", menu)

# ------------------ Add Expense ------------------
if choice == "Add Expense":
    st.subheader("Add New Expense")
    with st.form("expense_form"):
        date = st.date_input("Date")
        category = st.selectbox("Category", ["Flight", "Hotel", "Food", "Transport", "Other"])
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        description = st.text_area("Description")
        location = st.text_input("Location")
        submitted = st.form_submit_button("Add Expense")
        
        if submitted:
            add_expense(date, category, amount, description, location)
            st.success("Expense Added Successfully!")

# ------------------ View Expenses ------------------
elif choice == "Analytics":
    st.markdown("<h2 style='text-align:center;color:#00BFFF;'>🌍 Real-Time Travel Expense Analytics Dashboard</h2>", unsafe_allow_html=True)
    df = get_expenses()

    if not df.empty:
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.strftime("%b %Y")

        # ---- KPIs ----
        total_expense = df['amount'].sum()
        avg_expense = df['amount'].mean()
        top_location = df.groupby('location')['amount'].sum().idxmax()
        top_spent = df.groupby('category')['amount'].sum().idxmax()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Total Expenses", f"₹{total_expense:,.2f}")
        with col2:
            st.metric("📊 Avg Expense", f"₹{avg_expense:,.2f}")
        with col3:
            st.metric("📍 Top Location", top_location)
        with col4:
            st.metric("🏷️ Top Category", top_spent)

        st.markdown("---")

        # ---- Category Pie Chart ----
        cat_fig = px.pie(df, names='category', values='amount', title="Expense Distribution by Category",
                         color_discrete_sequence=px.colors.qualitative.Bold)
        cat_fig.update_traces(textinfo='percent+label', pull=[0.05]*len(df['category']))
        st.plotly_chart(cat_fig, use_container_width=True)

        # ---- Monthly Trend ----
        monthly = df.groupby('month')['amount'].sum().reset_index()
        line_fig = px.line(monthly, x='month', y='amount', markers=True,
                           title="📆 Monthly Expense Trend", color_discrete_sequence=['#00BFFF'])
        line_fig.update_traces(line=dict(width=3))
        st.plotly_chart(line_fig, use_container_width=True)

        # ---- Location-based Heatmap ----
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="travel_expense_app")

            def get_coordinates(loc):
                try:
                    location = geolocator.geocode(loc)
                    if location:
                        return pd.Series([location.latitude, location.longitude])
                except:
                    return pd.Series([None, None])
                return pd.Series([None, None])

            if 'latitude' not in df.columns or 'longitude' not in df.columns:
                coords = df['location'].dropna().apply(get_coordinates)
                df[['latitude', 'longitude']] = coords

            map_data = df.dropna(subset=['latitude', 'longitude'])

            if not map_data.empty:
                st.markdown("### 🗺️ Location Heatmap of Expenses")
                map_fig = px.scatter_mapbox(
                    map_data,
                    lat="latitude",
                    lon="longitude",
                    size="amount",
                    color="category",
                    hover_name="location",
                    hover_data=["amount", "description"],
                    zoom=3,
                    color_discrete_sequence=px.colors.qualitative.Prism
                )
                map_fig.update_layout(
                    mapbox_style="carto-darkmatter",
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=500
                )
                st.plotly_chart(map_fig, use_container_width=True)
            else:
                st.warning("No valid location data found for map display.")
        except Exception as e:
            st.error(f"Map Error: {e}")

        st.markdown("---")

        # ---- Top Locations Chart ----
        loc_sum = df.groupby('location')['amount'].sum().reset_index().sort_values(by='amount', ascending=False)
        bar_fig = px.bar(loc_sum, x='location', y='amount',
                         title="🏙️ Top Spending Locations",
                         color='amount', color_continuous_scale='tealgrn')
        st.plotly_chart(bar_fig, use_container_width=True)
    else:
        st.info("No data available for analytics. Add some expenses first!")