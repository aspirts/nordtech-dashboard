
import streamlit as st
import pandas as pd
import plotly.express as px

# ================================================================
# LIETOŠANAS INSTRUKCIJA / ИНСТРУKЦИЯ ПО ЗАПУСКУ
# ================================================================
# LV: Lai palaistu šo lietotni, veiciet šādas darbības:
# 1. Pārliecinieties, ka Python ir instalēts jūsu datorā.
# 2. Atveriet termināli (CMD, PowerShell vai VS Code Terminal).
# 3. Instalējiet nepieciešamās bibliotēkas:
#    pip install streamlit pandas plotly
# 4. Pārejiet uz mapi, kurā atrodas fails 'app.py' un 'enriched_data.csv'.
# 5. Palaidiet lietotni ar komandu:
#    streamlit run app.py
# ================================================================

# 1. Iestatījumi
st.set_page_config(page_title="NordTech Analītika", layout="wide")
st.title("📊 NordTech Biznesa Diagnostika")

# 2. Datu ielāde
@st.cache_data
def load_data():
    df = pd.read_csv('enriched_data.csv')
    df['Date'] = pd.to_datetime(df['Date'])
    # Nodrošinām, ka kategorijās nav lieku atstarpju
    df['Product_Category'] = df['Product_Category'].str.strip()
    return df

try:
    df = load_data()

    # 3. Sidebar filtri
    st.sidebar.header("Filtri")
    all_cats = sorted(df['Product_Category'].unique().tolist())
    
    selected_category = st.sidebar.multiselect(
        "Izvēlies kategoriju:",
        options=all_cats,
        default=all_cats
    )

    # REAĢĒŠANA UZ FILTRU:
    # Ja nekas nav izvēlēts, rādām tukšu, ja ir - filtrējam
    if not selected_category:
        st.warning("Lūdzu, izvēlieties vismaz vienu kategoriju filtrā!")
        st.stop()
    
    filtered_df = df[df['Product_Category'].isin(selected_category)].copy()

    # 4. KPI rinda
    total_revenue = filtered_df['Price'].sum()
    return_count = filtered_df['Is_Returned'].sum()
    return_rate = (return_count / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
    complaint_count = len(filtered_df[filtered_df['Issue_Category'] != 'Nav sūdzību'])

    col1, col2, col3 = st.columns(3)
    col1.metric("Kopējie ieņēmumi", f"{total_revenue:,.2f} EUR")
    col2.metric("Atgriešanu %", f"{return_rate:.2f}%")
    col3.metric("Sūdzību skaits", complaint_count)

    st.divider()

    # 5. Vizuāļi
    left_col, right_col = st.columns(2)

    with left_col:
        st.subheader("Sūdzību iemesli")
        # Svarīgi: norādām kolonnu nosaukumus precīzi
        issue_data = filtered_df[filtered_df['Issue_Category'] != 'Nav sūdzību']['Issue_Category'].value_counts().reset_index()
        issue_data.columns = ['Iemesls', 'Skaits'] # Pārsaucam skaidrības labad
        
        if not issue_data.empty:
            fig_issues = px.bar(
                issue_data, x='Skaits', y='Iemesls', orientation='h',
                color='Iemesls', title="Biežākās problēmas",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            # Šī rinda nodrošina, ka grafiks reaģē uz izmaiņām
            st.plotly_chart(fig_issues, use_container_width=True, key="issues_chart")
        else:
            st.info("Šajā kategorijā sūdzību nav.")

    with right_col:
        st.subheader("Ieņēmumi vs. Zaudējumi")
        fin_data = filtered_df.groupby('Product_Category').agg({'Price': 'sum', 'Refund_Amount': 'sum'}).reset_index()
        
        fig_fin = px.bar(
            fin_data, x='Product_Category', y=['Price', 'Refund_Amount'],
            barmode='group', title="Finansiālā ietekme",
            labels={'value': 'EUR', 'variable': 'Veids'}
        )
        st.plotly_chart(fig_fin, use_container_width=True, key="fin_chart")

    # 6. Datu tabula
    st.subheader("Problemātiskie pasūtījumi (Top 10)")
    st.dataframe(filtered_df[filtered_df['Is_Returned'] == 1][['Transaction_ID', 'Product_Name', 'Price', 'Issue_Category']].head(10), use_container_width=True)

except Exception as e:
    st.error(f"Kļūda: {e}")
