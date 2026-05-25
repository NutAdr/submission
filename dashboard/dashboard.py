import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

st.title('Dashboard Analisis E-Commerce Public Dataset')

orders_df = pd.read_csv("orders_dataset.csv")
customer_df = pd.read_csv("customers_dataset.csv")
reviews_df = pd.read_csv("order_reviews_dataset.csv")
items_df = pd.read_csv("order_items_dataset.csv")
products_df = pd.read_csv("products_dataset.csv")
payments_df = pd.read_csv("order_payments_dataset.csv")

orders_df_clean = orders_df.dropna(subset=['order_approved_at', 'order_delivered_carrier_date', 'order_delivered_customer_date'])

datetime_columns = [
    'order_purchase_timestamp', 'order_approved_at', 
    'order_delivered_carrier_date', 'order_delivered_customer_date', 
    'order_estimated_delivery_date'
]
for col in datetime_columns:
    orders_df_clean[col] = pd.to_datetime(orders_df_clean[col])

with st.sidebar :
  with st.sidebar:
    st.title("Menu")
    menu = st.radio("Pindah Menu:", ["Pertanyaan Bisnis 1", "Pertanyaan Bisnis 2", "Pertanyaan Bisnis 3", "Analisis Lanjutan", "Conclusion & Recomendation"])

if menu == "Pertanyaan Bisnis 1":
    st.subheader("Berapa persentase pelanggan (Customer Unique ID) yang melakukan pembelian ulang (repeat order) lebih dari 1 kali di negara bagian São Paulo (SP) dibandingkan Rio de Janeiro (RJ) sepanjang tahun 2017?")

    orders_2017 = orders_df_clean[orders_df_clean['order_purchase_timestamp'].dt.year == 2017]

    customer_orders_2017 = pd.merge(
        orders_2017,
        customer_df,
        on="customer_id",
        how="inner"
    )

    eda_q1 = customer_orders_2017[customer_orders_2017['customer_state'].isin(['SP', 'RJ'])]

    order_counts = eda_q1.groupby(['customer_state', 'customer_unique_id']).size().reset_index(name='total_orders')

    order_counts['is_repeat'] = order_counts['total_orders'] > 1

    repeat_summary = order_counts.groupby('customer_state')['is_repeat'].value_counts(normalize=True).unstack() * 100

    fig, ax = plt.subplots(figsize=(7, 5))
    
    repeat_summary.plot(kind='bar', stacked=True, color=['#4e79a7', '#a0cbe8'], edgecolor='black', ax=ax)
    
    ax.set_title('Perbandingan Single Order vs Repeat Order (2017)')
    ax.set_ylabel('Persentase (%)')
    ax.set_xlabel('Negara Bagian (State)')
    ax.set_xticklabels(repeat_summary.index, rotation=0) 
    ax.legend(['Single Order', 'Repeat Order'], loc='lower left')
    plt.tight_layout()
    
    st.pyplot(fig)

    with st.expander("Insight"):
      st.write('''
        Per tahun 2017, ternyata untuk state customer yang berada di (RJ) Rio de Janeiro dan (SP) Sao Paolo sama-sama sedikit yang melakukan repeat order hanya berkisaran 2.7-2.8%, mayoritas hanya melakukan single order saja kisaran 97% sehingga bisa menjadi perhatian dan dipersiapkan planning / skema untuk kedua state tersebut karena tingkat retensi kedua state tersebut sangatlah rendah
      ''')
    
    
elif menu == "Pertanyaan Bisnis 2":
    st.subheader("Apakah rata-rata skor ulasan (Review Score) untuk kategori produk 'cama_mesa_banho' mengalami penurunan di bawah 4.0 bintang akibat keterlambatan pengiriman (waktu pengiriman aktual melebihi estimasi) selama periode kuartal pertama (Q1) tahun 2018?")
   

    q1_2018_orders = orders_df_clean[
        (orders_df_clean['order_purchase_timestamp'] >= '2018-01-01') &
        (orders_df_clean['order_purchase_timestamp'] <= '2018-03-31')
    ]

    q1_2018_orders['is_delayed'] = q1_2018_orders['order_delivered_customer_date'] > q1_2018_orders['order_estimated_delivery_date']

    merge_step1 = pd.merge(q1_2018_orders, items_df, on='order_id', how='inner')
    merge_step2 = pd.merge(merge_step1, products_df, on='product_id', how='inner')
    eda_q2 = pd.merge(merge_step2, reviews_df, on='order_id', how='inner')

    eda_q2_filtered = eda_q2[eda_q2['product_category_name'] == 'cama_mesa_banho']

    review_by_delivery = eda_q2_filtered.groupby('is_delayed')['review_score'].agg(['mean', 'count', 'median'])
    

    plot_data = review_by_delivery.reset_index()

    plot_data['is_delayed'] = plot_data['is_delayed'].map({False: 'Tepat Waktu', True: 'Terlambat'})

    fig, ax = plt.subplots(figsize=(6, 5))

   
    sns.barplot(x='is_delayed', y='mean', data=plot_data, palette=['#2ca02c', '#d62728'], ax=ax)

    
    ax.set_title("Rata-rata Rating Kategori 'cama_mesa_banho' (Q1 2018)")
    ax.set_ylabel('Skor Ulasan (1-5 Bintang)')
    ax.set_xlabel('Status Logistik Pengiriman')
    ax.set_ylim(0, 5)

   
    for index, row in plot_data.iterrows():
        ax.text(index, row['mean'] + 0.1, f"{row['mean']:.2f}", ha='center', fontweight='bold')

    plt.tight_layout()
    
    st.pyplot(fig)

    with st.expander("Insight"):
      st.write('''
        Per Q1 tahun 2018, ketika suatu barang sampai kepada pelanggan delayed dari estimasi sampainya memungkinkan untuk mempengaruhi kepuasan pelanggan. Terlihat dari is_delayed = True, ketika analisis mean dan mediannya, ternyata rata-rata ratingnya sebesar 2.3 dan nilai tengahnya 1.0 (dimana rendah sekali) untuk 350 data. Di sisi lain, ketika tidak delay rata-rata review nya cukup besar yaitu 3.9 dengan median 5.0 untuk 1931 data. Yang perlu di take note bahwa ada perbedaan jumlah data yang cukup besar (selisih data = 1581 data) sehingga bisa dicek dari sisi lain juga, tidak bisa langsung dikatakan positif pasti pengaruh.
      ''')
    
elif menu == "Pertanyaan Bisnis 3":
    st.subheader("Berapa kontribusi nilai transaksi (Payment Value) dan jumlah cicilan (Payment Installments) dengan menggunakan metode 'credit_card' pada kategori produk bernilai tinggi seperti 'watches_gifts' selama periode semester kedua (H2) tahun 2017?")
    
    h2_2017_orders = orders_df_clean[
    (orders_df_clean['order_purchase_timestamp'] >= '2017-07-01') &
    (orders_df_clean['order_purchase_timestamp'] <= '2017-12-31')
    ]

    m1 = pd.merge(h2_2017_orders, payments_df, on='order_id', how='inner')
    m2 = pd.merge(m1, items_df, on='order_id', how='inner')
    eda_q3 = pd.merge(m2, products_df, on='product_id', how='inner')

    eda_q3_filtered = eda_q3[
        (eda_q3['payment_type'] == 'credit_card') &
        (eda_q3['product_category_name'] == 'relogios_presentes')
    ]

    total_payment_value = eda_q3_filtered['payment_value'].sum()

    installments_distribution = eda_q3_filtered['payment_installments'].value_counts().sort_index()

    plot_data_q3 = installments_distribution.reset_index()
    plot_data_q3.columns = ['Tenor Cicilan (Bulan)', 'Jumlah Transaksi']

   
    fig, ax = plt.subplots(figsize=(9, 5))

    
    sns.barplot(x='Tenor Cicilan (Bulan)', y='Jumlah Transaksi', data=plot_data_q3.head(10), color='#ff7f0e', ax=ax)

    
    ax.set_title("Jumlah Transaksi 'watches_gifts' Berdasarkan Durasi Cicilan (H2 2017)")
    ax.set_ylabel('Jumlah Transaksi')
    ax.set_xlabel('Lama Cicilan (Bulan)')

    
    for index, row in plot_data_q3.head(10).iterrows():
        ax.text(index, row['Jumlah Transaksi'] + 5, f"{int(row['Jumlah Transaksi'])}", ha='center', fontweight='bold')

    plt.tight_layout()

   
    st.pyplot(fig)

    with st.expander("Insight"):
      st.write('''
        Pada semester kedua tahun 2017 (H2 2017), total transaksi kategori Watches Gifts  metode pembayaran kartu kredit mencapai sekitar 334 ribu. Mayoritas pelanggan memilih pembayaran dengan cicilan rendah, terutama 1–4 kali cicilan, yang menunjukkan kecenderungan pelanggan untuk melunasi pembayaran lebih cepat.
        Ada sebagian pelanggan yang memilih cicilan lebih panjang seperti 8 dan 10 kali, yang mengindikasikan adanya kebutuhan fleksibilitas pembayaran pada produk kategori ini. Hal ini dapat menjadi peluang bagi perusahaan untuk menawarkan promo cicilan atau kerja sama kartu kredit guna meningkatkan daya beli pelanggan.
      ''')
   

elif menu == "Analisis Lanjutan":
    st.subheader("RFM Analysis")
    rfm_df = pd.merge(
    orders_df_clean,
    payments_df,
    on='order_id',
    how='inner'
    )


    ambil_date = rfm_df['order_purchase_timestamp'].max()

   
    recency = rfm_df.groupby('customer_id')['order_purchase_timestamp'].max().reset_index()
    recency['Recency'] = (ambil_date - recency['order_purchase_timestamp']).dt.days

   
    frequency = rfm_df.groupby('customer_id')['order_id'].count().reset_index()
    frequency.columns = ['customer_id', 'Frequency']

   
    monetary = rfm_df.groupby('customer_id')['payment_value'].sum().reset_index()
    monetary.columns = ['customer_id', 'Monetary']

    rfm = pd.merge(recency[['customer_id', 'Recency']], frequency, on='customer_id')
    rfm = pd.merge(rfm, monetary, on='customer_id')

  
    col1, col2, col3 = st.columns(3)

   
    with col1:
        fig1, ax1 = plt.subplots(figsize=(6, 4))
        ax1.hist(rfm['Recency'], bins=30, color='orange')
        ax1.set_title('Distribusi Recency')
        ax1.set_xlabel('Hari Sejak Transaksi Terakhir')
        ax1.set_ylabel('Jumlah Customer')
        plt.tight_layout()
        st.pyplot(fig1)

    
    with col2:
        fig2, ax2 = plt.subplots(figsize=(6, 4))
        ax2.hist(rfm['Frequency'], bins=30, color='green')
        ax2.set_title('Distribusi Frequency')
        ax2.set_xlabel('Jumlah Transaksi')
        ax2.set_ylabel('Jumlah Customer')
        plt.tight_layout()
        st.pyplot(fig2)

   
    with col3:
        fig3, ax3 = plt.subplots(figsize=(6, 4))
        ax3.hist(rfm['Monetary'], bins=30, color='blue')
        ax3.set_title('Distribusi Monetary')
        ax3.set_xlabel('Total Pengeluaran')
        ax3.set_ylabel('Jumlah Customer')
        plt.tight_layout()
        st.pyplot(fig3)

    with st.expander("Insight"):
      st.write('''
        Beberapa customer memiliki nilai Frequency = 1, yang menunjukkan bahwa mereka hanya melakukan satu kali transaksi. Selain itu, nilai Recency yang cukup besar pada beberapa customer (misalnya 400–500 hari) mengindikasikan customer tersebut sudah lama tidak melakukan pembelian kembali. Dari Monetary, total pengeluaran customer cukup bervariasi. Hal ini menunjukkan adanya perbedaan nilai kontribusi pelanggan terhadap bisnis.Sebagian pelanggan cenderung belum menjadi pelanggan loyal karena masih jarang melakukan repeat order dan sebagian sudah cukup lama tidak aktif bertransaksi.
      ''')

elif menu == "Conclusion & Recomendation":
        st.subheader("Conclusion")
        st.write('''
          - Conclusion pertanyaan 1: Pada analisis repeat order customer di state Rio de Janeiro (RJ) dan São Paulo (SP) tahun 2017, mayoritas pelanggan hanya melakukan satu kali transaksi dengan persentase sekitar 97%. Hal ini menunjukkan tingkat retensi pelanggan masih rendah dan repeat order belum optimal.
          - Conclusion pertanyaan 2: Pada analisis keterlambatan pengiriman kategori camo_mesa_banho, pelanggan yang menerima pesanan melebihi estimasi pengiriman cenderung memberikan skor ulasan lebih rendah dibanding pelanggan yang menerima pesanan tepat waktu. Hal ini menunjukkan bahwa ketepatan pengiriman berpotensi pengaruh terhadap kepuasan pelanggan.
          - Conculusion pertanyaan 3: Pada analisis transaksi kategori Watches Gifts di semester kedua 2017, mayoritas pelanggan menggunakan pembayaran kartu kredit dengan cicilan rendah (1–4 kali). Namun, sebagian pelanggan juga memilih cicilan lebih panjang sehingga menunjukkan adanya kebutuhan fleksibilitas pembayaran.
          - Conclusion analisis lanjutan: Dari hasil RFM Analysis, sebagian besar pelanggan memiliki nilai Frequency yang rendah dan Recency yang cukup tinggi, yang berarti banyak pelanggan jarang melakukan transaksi ulang dan sudah cukup lama tidak aktif berbelanja. Selain itu, nilai Monetary yang bervariasi menunjukkan adanya perbedaan kontribusi pelanggan terhadap total pendapatan perusahaan.
        ''')
        st.subheader("Recommendation")
        st.write('''
          - Meningkatkan kualitas dan ketepatan pengiriman barang, terutama pada kategori produk yang sensitif terhadap keterlambatan, agar kepuasan pelanggan tetap terjaga dan review negatif dapat dikurangi.
          - Membuat strategi customer retention seperti program loyalitas, voucher repeat order, promo pelanggan lama, ataupun personalisasi rekomendasi produk untuk meningkatkan jumlah pelanggan yang melakukan transaksi ulang.
          - Menawarkan promo cicilan dan kerja sama dengan penyedia kartu kredit karena pelanggan pada kategori tertentu terlihat cukup tertarik menggunakan metode pembayaran cicilan.
          - Memanfaatkan hasil RFM Analysis untuk segmentasi pelanggan, misalnya:
          pelanggan aktif dan bernilai tinggi dapat diberikan reward atau promo eksklusif,
          pelanggan yang sudah lama tidak aktif dapat diberikan campaign re-engagement,
          pelanggan baru dapat diberikan onboarding promo agar lebih berpotensi menjadi pelanggan loyal.
          - Melakukan analisis lanjutan secara berkala agar perusahaan dapat memahami perubahan perilaku pelanggan dan menentukan strategi bisnis yang lebih tepat sasaran.
        ''')
    
