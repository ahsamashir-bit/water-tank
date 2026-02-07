import sys
import pandas as pd
import streamlit as st
import plotly.express as px


def load_data(path: str = 'Daily_Water_Intake.csv') -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception as e:
        st.error(f"READ_ERROR: {e}")
        sys.exit(1)

    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'])
    else:
        # No explicit Date column — we'll create a record index and continue.
        df.insert(0, 'Record', range(1, len(df) + 1))

    # Normalize possible water intake column names to `Water_Intake`
    candidates = [
        'Water_Intake',
        'Water Intake',
        'Daily Water Intake',
        'Daily Water Intake (liters)',
        'Daily Water Intake (ml)',
        'Daily_Water_Intake',
        'Daily-Water-Intake'
    ]
    found = None
    lower_cols = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower_cols:
            found = lower_cols[cand.lower()]
            break
    if found is None:
        # fallback: try to find any numeric column that looks like intake
        numeric_cols = df.select_dtypes('number').columns.tolist()
        if numeric_cols:
            found = numeric_cols[0]
    if found:
        df = df.rename(columns={found: 'Water_Intake'})
        df['Water_Intake'] = pd.to_numeric(df['Water_Intake'], errors='coerce').fillna(0)
    else:
        df['Water_Intake'] = 0

    if 'Water_Intake' in df.columns:
        df['Water_Intake'] = pd.to_numeric(df['Water_Intake'], errors='coerce').fillna(0)
    else:
        df['Water_Intake'] = 0

    if 'Hashtags' in df.columns:
        df['Hashtags'] = df['Hashtags'].fillna('')
    else:
        df['Hashtags'] = ''

    return df


def main():
    st.title('Daily Water Intake')
    data = load_data()

    st.write('Columns:', list(data.columns))
    st.write(data.head())

    # Sidebar filters and view selection
    st.sidebar.header('Filter Data')
    if 'Date' in data.columns:
        min_date = data['Date'].min()
        max_date = data['Date'].max()
        selected_date = st.sidebar.date_input('Select Date', value=min_date, min_value=min_date, max_value=max_date)
        selected_date = pd.to_datetime(selected_date)
        filtered_data = data[data['Date'] == selected_date]

        # Main dashboard
        st.header(f"Water Intake on {selected_date.strftime('%Y-%m-%d')}")
        total_intake = filtered_data['Water_Intake'].sum()
        average_intake = filtered_data['Water_Intake'].mean() if not filtered_data.empty else 0
        st.metric(label='Total Water Intake', value=f"{total_intake:.2f}")
        st.metric(label='Average Water Intake', value=f"{average_intake:.2f}")

        # Time series plot
        fig = px.line(data, x='Date', y='Water_Intake', title='Daily Water Intake Over Time')
        fig.update_layout(xaxis_title='Date', yaxis_title='Water Intake', template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    else:
        # No Date column — use Record index for simple exploration
        min_rec = int(data['Record'].min())
        max_rec = int(data['Record'].max())
        rec_range = st.sidebar.slider('Record range', min_rec, max_rec, (min_rec, max_rec))
        start, end = rec_range
        filtered_data = data[(data['Record'] >= start) & (data['Record'] <= end)]

        st.header(f"Water Intake for records {start}–{end}")
        total_intake = filtered_data['Water_Intake'].sum()
        average_intake = filtered_data['Water_Intake'].mean() if not filtered_data.empty else 0
        st.metric(label='Total Water Intake', value=f"{total_intake:.2f}")
        st.metric(label='Average Water Intake', value=f"{average_intake:.2f}")

        fig = px.line(data, x='Record', y='Water_Intake', title='Water Intake by Record')
        fig.update_layout(xaxis_title='Record', yaxis_title='Water Intake', template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)

    # Hashtag counts
    hashtag_counts = (
        data['Hashtags']
        .str.split(',')
        .explode()
        .str.strip()
        .replace('', pd.NA)
        .dropna()
        .value_counts()
        .reset_index()
    )
    if not hashtag_counts.empty:
        hashtag_counts.columns = ['Hashtag', 'Count']
        fig2 = px.bar(hashtag_counts, x='Hashtag', y='Count', title='Hashtag Usage Frequency')
        fig2.update_layout(xaxis_title='Hashtag', yaxis_title='Count', template='plotly_white')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info('No hashtags to display.')


if __name__ == '__main__':
    main()

