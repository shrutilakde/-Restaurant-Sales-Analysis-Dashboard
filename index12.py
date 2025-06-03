import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- Load Data ---
@st.cache_data
def load_data(file_path):
    file_path = "Items.xlsx"
    df = pd.read_excel(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

df = load_data("your_restaurant_data.xlsx") # Replace with your actual file name

# --- Title ---
st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🍽️ Restaurant Sales Analysis Dashboard 📊</h1>", unsafe_allow_html=True)
st.markdown("<hr style='border: 2px solid #f0f2f6;'>", unsafe_allow_html=True)

# --- Sidebar for Selections ---
st.sidebar.header("Analysis Options")
selected_items = st.sidebar.multiselect("Select Item(s)", df['Item'].unique())
time_period = st.sidebar.radio("View By", ["Yearly", "Monthly", "Weekly"])
chart_types = st.sidebar.multiselect("Select Chart(s)", ["Bar Chart", "Line Chart", "Scatter Plot"], default=["Bar Chart", "Line Chart"])

st.sidebar.subheader("Top Items Analysis")
top_items_view = st.sidebar.radio("View Top Items By", ["Overall", "Yearly", "Monthly", "Weekly"])
top_n = st.sidebar.slider("Number of Top Items to Show", min_value=1, max_value=10, value=5)

st.sidebar.subheader("Optional Filters")
date_range = st.sidebar.date_input("Select Date Range", [df['Date'].min().date(), df['Date'].max().date()])

# --- Data Filtering ---
filtered_df = df.copy()
if selected_items:
    filtered_df = filtered_df[filtered_df['Item'].isin(selected_items)].copy()
if len(date_range) == 2:
    start_date, end_date = date_range
    start_timestamp = pd.to_datetime(start_date)
    end_timestamp = pd.to_datetime(end_date)
    filtered_df = filtered_df[(filtered_df['Date'] >= start_timestamp) & (filtered_df['Date'] <= end_timestamp)].copy()

# --- Data Aggregation for Analysis ---
grouped_df = pd.DataFrame()
if not filtered_df.empty:
    if time_period == "Yearly":
        filtered_df['Time'] = filtered_df['Date'].dt.year
    elif time_period == "Monthly":
        filtered_df['Time'] = filtered_df['Date'].dt.to_period('M').astype(str)
    elif time_period == "Weekly":
        filtered_df['Time'] = filtered_df['Date'].dt.isocalendar().week.astype(str) + '-' + filtered_df['Date'].dt.year.astype(str)
        filtered_df['week_num'] = filtered_df['Date'].dt.isocalendar().week
        filtered_df['year'] = filtered_df['Date'].dt.year
        filtered_df = filtered_df.sort_values(by=['year', 'week_num'])
        filtered_df.drop(columns=['week_num', 'year'], inplace=True)

    grouped_df = filtered_df.groupby('Time').agg({'Total (₹)': 'sum', 'Qty.': 'sum'}).reset_index()

# --- Sale Analysis Section ---
st.subheader(f"Sale Analysis for: {', '.join(selected_items) if selected_items else 'All Items'} (Viewed {time_period})")

if "Bar Chart" in chart_types:
    if not grouped_df.empty:
        fig_bar = px.bar(grouped_df, x='Time', y='Total (₹)', title=f'Total Sales per {time_period}')
        st.plotly_chart(fig_bar)
    else:
        st.warning("No data to display for the bar chart based on the current selection.")

if "Scatter Plot" in chart_types:
    if not filtered_df.empty:
        fig_scatter = px.scatter(filtered_df, x='Date', y='Total (₹)', title='Daily Sales Scatter Plot')
        st.plotly_chart(fig_scatter)
        st.info("Scatter Plot shows the distribution of daily sales.")
    else:
        st.warning("No data to display for the scatter plot based on the current selection.")

# --- Sale Trend Prediction Section ---
st.subheader("Sale Trend Prediction")
trend_conclusion = ""

if "Line Chart" in chart_types:
    if not grouped_df.empty:
        fig_line = px.line(grouped_df, x='Time', y='Total (₹)', title=f'Sales Trend ({time_period})')
        st.plotly_chart(fig_line)

        st.subheader("Sale Trend Prediction (Simple Moving Average)")
        if len(grouped_df) > 1:
            window = st.slider("Moving Average Window", min_value=2, max_value=len(grouped_df) // 2 if len(grouped_df) > 2 else 2, value=min(5, len(grouped_df) - 1))
            grouped_df['SMA'] = grouped_df['Total (₹)'].rolling(window=window, min_periods=1).mean()
            fig_line_pred = px.line(grouped_df, x='Time', y=['Total (₹)', 'SMA'], title=f'Sales Trend with Simple Moving Average ({time_period})')
            st.plotly_chart(fig_line_pred)

            # --- Analyze Sales Trend in Words ---
            last_sales = grouped_df['Total (₹)'].iloc[-1]
            previous_sales = grouped_df['Total (₹)'].iloc[-2] if len(grouped_df) > 1 else last_sales
            sales_change = last_sales - previous_sales

            if sales_change > 0:
                trend_conclusion = f"The sales trend shows an increasing pattern in the recent {time_period}."
            elif sales_change < 0:
                trend_conclusion = f"The sales trend indicates a decreasing pattern in the recent {time_period}."
            else:
                trend_conclusion = f"The sales trend appears relatively stable in the recent {time_period}."

            if 'SMA' in grouped_df.columns and not grouped_df['SMA'].isnull().all():
                last_sma = grouped_df['SMA'].iloc[-1]
                if last_sales > last_sma:
                    trend_conclusion += " Current sales are above the average trend."
                elif last_sales < last_sma:
                    trend_conclusion += " Current sales are below the average trend."
                else:
                    trend_conclusion += " Current sales are in line with the average trend."

        else:
            st.warning("Not enough data points for a meaningful trend prediction.")
            trend_conclusion = "Insufficient data to analyze the sales trend effectively."

    else:
        st.warning("No data to display the sales trend for the current selection.")
        trend_conclusion = "No sales data available for the current selection."

# --- Sale Trend Prediction Description ---
if "Line Chart" in chart_types and not grouped_df.empty and len(grouped_df) > 1:
    st.subheader("Sale Trend Prediction Description")
    st.info(trend_conclusion)
elif "Line Chart" in chart_types and (grouped_df.empty or len(grouped_df) <= 1):
    st.subheader("Sale Trend Prediction Description")
    st.info("Not enough data to generate a meaningful sales trend prediction description.")
elif "Line Chart" not in chart_types:
    pass # Don't show the description if Line Chart is not selected

# --- Top Items Analysis ---
st.subheader(f"Top {top_n} Most Sold Items (Viewed by {top_items_view})")

if top_items_view == "Overall":
    top_items = df.groupby('Item')['Qty.'].sum().nlargest(top_n).reset_index()
    if not top_items.empty:
        st.dataframe(top_items)
    else:
        st.warning("No sales data available to determine the top items.")
elif top_items_view == "Yearly":
    df['Year'] = df['Date'].dt.year
    top_items = df.groupby(['Year', 'Item'])['Qty.'].sum().nlargest(top_n).reset_index()
    if not top_items.empty:
        st.dataframe(top_items)
    else:
        st.warning("No yearly sales data available to determine the top items.")
elif top_items_view == "Monthly":
    df['Month'] = df['Date'].dt.to_period('M').astype(str)
    top_items = df.groupby(['Month', 'Item'])['Qty.'].sum().nlargest(top_n).reset_index()
    if not top_items.empty:
        st.dataframe(top_items)
    else:
        st.warning("No monthly sales data available to determine the top items.")
elif top_items_view == "Weekly":
    df['Week-Year'] = df['Date'].dt.isocalendar().week.astype(str) + '-' + df['Date'].dt.year.astype(str)
    top_items = df.groupby(['Week-Year', 'Item'])['Qty.'].sum().nlargest(top_n).reset_index()
    if not top_items.empty:
        st.dataframe(top_items)
    else:
        st.warning("No weekly sales data available to determine the top items.")

# --- Additional Feature: Overall Sales Statistics ---
st.subheader("Overall Sales Statistics")
if not df.empty:
    total_revenue = df['Total (₹)'].sum()
    average_order_value = df['Total (₹)'].mean()
    total_items_sold = df['Qty.'].sum()
    st.metric("Total Revenue", f"₹ {total_revenue:,.2f}")
    st.metric("Average Order Value", f"₹ {average_order_value:,.2f}")
    st.metric("Total Items Sold", f"{total_items_sold}")
else:
    st.warning("No overall sales data available.")