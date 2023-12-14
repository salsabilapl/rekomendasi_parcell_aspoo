import streamlit as st
import pandas as pd
from ortools.linear_solver import pywraplp
import random
import numpy as np
import base64 
from base64 import b64encode
from io import BytesIO 

# Fungsi untuk menyelesaikan Knapsack Problem
def knapsack_solver(df, max_price, max_weight, min_rating):
    solver = pywraplp.Solver.CreateSolver('SCIP')

    # Menambahkan variabel biner untuk setiap produk
    x = {}
    for i in range(len(df)):
        x[i] = solver.BoolVar('x[%i]' % i)

    # Menetapkan fungsi tujuan (maksimalkan total rating)
    objective = solver.Objective()
    for i in range(len(df)):
        objective.SetCoefficient(x[i], df['Rating'].iloc[i])
    objective.SetMaximization()

    # Menetapkan batasan harga, berat, dan minimal rating
    price_constraint = solver.Constraint(0, max_price)
    weight_constraint = solver.Constraint(0, max_weight)
    rating_constraint = solver.Constraint(min_rating, solver.infinity())

    for i in range(len(df)):
        price_constraint.SetCoefficient(x[i], df['Price'].iloc[i])
        weight_constraint.SetCoefficient(x[i], df['Weight'].iloc[i])
        rating_constraint.SetCoefficient(x[i], df['Rating'].iloc[i])

    # Menetapkan batasan minimal satu produk dipilih untuk setiap kategori
    categories = df['Product_Category'].unique()
    for category in categories:
      category_df = df[df['Product_Category'] == category]
      category_constraint = solver.Constraint(1, solver.infinity())  # Minimal satu produk yang dipilih
      for i in range(len(category_df)):
        category_constraint.SetCoefficient(x[df.index.get_loc(category_df.index[i])], 1)

    # Menyelesaikan masalah
    solver.Solve()

    # Menyimpan hasil ke dalam DataFrame baru
    selected_products = pd.DataFrame(columns=df.columns)
    for i in range(len(df)):
        if x[i].solution_value():
            selected_products = pd.concat([selected_products, df.iloc[[i]]], ignore_index=True)

    return selected_products

# Load data
df = pd.read_excel('OutputAspoo.xlsx')
dataset = df[['kota_nama','nama_barang','harga_umum','name','kategori']]
num_records = len(dataset)
data = {
    'Rating': np.random.uniform(low=3.0, high=5.0, size=num_records).round(2),
    'Weight': np.random.uniform(low=0.1, high=2.0, size=num_records).round(2),
}


#Preprocessing data
data_rating = pd.DataFrame(data)
dataset_final = dataset.join(data_rating)
dataset_final.rename(columns={'kategori':'Product_Category','nama_barang': 'Item', 'harga_umum': 'Price'}, inplace=True)
dataset_final = dataset_final.dropna()
dataset_final['Price'] = dataset_final['Price'].astype(int).astype(float)
dataset_final['Price'] = dataset_final['Price'].div(1000)


# Tampilan Streamlit
st.title('Aplikasi Rekomendasi Parcell ASPOO')

# Input field untuk memasukkan kota
selected_city = st.selectbox('Pilih Nama Kota', df['kota_nama'].unique())

# Input field untuk batasan harga, berat, dan minimal rating
max_price = st.number_input('Batasan Harga Maksimal (... ribu)', min_value=0, value=200)
max_weight = st.number_input('Batasan Berat Maksimal (... kg)', min_value=0, value=10)
min_rating = st.number_input('Minimal Rating', min_value=0, max_value=5, value=4)

# Tombol untuk memproses
if st.button('Proses'):
    # Filter berdasarkan kota yang dimasukkan
    df_kota = dataset_final.loc[dataset_final['kota_nama']==selected_city]
    df_kota_final = df_kota[['name','Item','Price','Product_Category','Rating','Weight']]

    # Memanggil fungsi knapsack_solver
    result_df = knapsack_solver(df_kota_final, max_price, max_weight, min_rating)

    # Menampilkan hasil
    st.markdown('### Hasil Rekomendasi Parcell ASPOO')
    renamed_columns = {
        'name': 'Nama Produk',
        'Item': 'Barang',
        'Price': 'Harga',
        'Product_Category': 'Kategori Produk',
        'Rating': 'Rating',
        'Weight': 'Berat'
    }
    result_df.rename(columns=renamed_columns, inplace=True)
    st.write(result_df)
    
    # Menyimpan hasil ke dalam file CSV
    st.markdown('### Unduh Hasil Rekomendasi Parcell ASPOO')
    result_df.reset_index().drop("index", axis = 1, inplace = True)
    csv = result_df
    csv_download = csv.to_csv(index=False)
    href = f'<a href="data:file/csv;base64,{b64encode(csv_download.encode()).decode()}" download="hasil_parcell_ASPOO2023.csv">Unduh File</a>'
    st.markdown(href, unsafe_allow_html=True)
