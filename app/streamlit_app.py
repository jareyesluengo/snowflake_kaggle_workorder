# libraries

# import os
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime

from snowflake.snowpark.context import get_active_session

# Get the current credentials
session = get_active_session()

# Page configuration
st.set_page_config(
    page_title="Equipment Failure Analysis",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title and description
st.title("🔧 Equipment Failure Analysis Dashboard")
st.markdown("Analyze equipment failures, maintenance issues, and technical assignments across your systems.")

# Sample data - in your real app, you'll load this from CSV or database
def load_data():
    df_table = session.table("KAGGLE_DATABASE.MAINTENANCE_DATASETS.MAINTENANCE_FAILURE_VIEW")
    # path_out =  '../data/output/'
    return df_table.to_pandas() # pd.read_csv(os.path.join(path_out, 'local_test.csv')) # 

# Load data
df = load_data()
df['DATE_RECEIVED'] = pd.to_datetime(df['DATE_RECEIVED'])

# Sidebar filters
st.sidebar.header("🔍 Filters")

# Machine filter
machines = ['All'] + sorted(df['MACH'].unique())
selected_machine = st.sidebar.selectbox('Select Machine', machines)

# System class filter
systems = ['All'] + sorted(df['SYSTEM_CLASS'].unique())
selected_system = st.sidebar.selectbox('Select System', systems)

# Failure mode filter
failure_modes = ['All'] + sorted(df['FAILURE_MODE'].unique())
selected_failure_mode = st.sidebar.selectbox('Select Failure Mode', failure_modes)

# Technician filter (handle multiple technicians)
all_techs = set()
for tech_list in df['TECH'].str.split(', '):
    all_techs.update(tech_list)
techs = ['All'] + sorted(all_techs)
selected_tech = st.sidebar.selectbox('Select Technician', techs)

# Date range filter
min_date = df['DATE_RECEIVED'].min()
max_date = df['DATE_RECEIVED'].max()
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

# Apply filters
filtered_df = df.copy()

if selected_machine != 'All':
    filtered_df = filtered_df[filtered_df['MACH'] == selected_machine]

if selected_system != 'All':
    filtered_df = filtered_df[filtered_df['SYSTEM_CLASS'] == selected_system]

if selected_failure_mode != 'All':
    filtered_df = filtered_df[filtered_df['FAILURE_MODE'] == selected_failure_mode]

if selected_tech != 'All':
    filtered_df = filtered_df[filtered_df['TECH'].str.contains(selected_tech, na=False)]

if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (filtered_df['DATE_RECEIVED'] >= pd.Timestamp(start_date)) & 
        (filtered_df['DATE_RECEIVED'] <= pd.Timestamp(end_date))
    ]

# Main dashboard
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Records", len(filtered_df))
    
with col2:
    st.metric("Unique Machines", filtered_df['MACH'].nunique())
    
with col3:
    st.metric("Failure Types", filtered_df['FAILURE_MODE'].nunique())

# Visualizations
st.subheader("📊 Data Visualizations")

viz_col1, viz_col2 = st.columns(2)

with viz_col1:
    # Failures by system
    system_failures = filtered_df['SYSTEM_CLASS'].value_counts()
    fig1 = px.bar(
        system_failures,
        title="Failures by System Class",
        labels={'value': 'Number of Failures', 'index': 'System Class'}
    )
    st.plotly_chart(fig1, use_container_width=True)

with viz_col2:
    # Failures over time
    time_series = filtered_df.groupby('DATE_RECEIVED').size().reset_index(name='count')
    fig2 = px.line(
        time_series,
        x='DATE_RECEIVED',
        y='count',
        title="Failures Over Time"
    )
    st.plotly_chart(fig2, use_container_width=True)

# Failure mode distribution
failure_dist = filtered_df['FAILURE_MODE'].value_counts()
fig3 = px.pie(
    failure_dist,
    values=failure_dist.values,
    names=failure_dist.index,
    title="Failure Mode Distribution"
)
st.plotly_chart(fig3, use_container_width=True)

# Detailed data table
st.subheader("📋 Detailed Failure Records")
st.dataframe(
    filtered_df,
    use_container_width=True,
    column_config={
        "DATE_RECEIVED": st.column_config.DateColumn("Date Received"),
        "ISSUE": st.column_config.TextColumn("Issue", width="large"),
        "INFO": st.column_config.TextColumn("Technical Info", width="large")
    },
    hide_index=True
)

# Export option
if st.button("📥 Export Filtered Data to CSV"):
    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name=f"failure_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv"
    )

# Technical analysis section
st.subheader("👥 Technician Analysis")
tech_workload = df['TECH'].str.split(', ').explode().value_counts()
fig4 = px.bar(
    tech_workload,
    title="Workload by Technician",
    labels={'value': 'Number of Assignments', 'index': 'Technician'}
)
st.plotly_chart(fig4, use_container_width=True) 