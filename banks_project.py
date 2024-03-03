from bs4 import BeautifulSoup
import requests
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime 

def log_progress(message): 
    timestamp_format = '%Y-%h-%d-%H:%M:%S' # Year-Monthname-Day-Hour-Minute-Second 
    now = datetime.now() # get current timestamp 
    timestamp = now.strftime(timestamp_format) 
    with open("./code_log.txt","a") as f: 
        f.write(timestamp + ' : ' + message + '\n')

def extract(url, table_attribs):
    page = requests.get(url).text
    data = BeautifulSoup(page, 'html.parser')
    df = pd.DataFrame(columns = table_attribs)
    tables = data.find_all('tbody')
    rows = tables[0].find_all('tr')

    for row in rows:
        col = row.find_all('td')
        if len(col) != 0:
            ae = col[1].find_all('a')
            data_dict = {
                'Name' : ae[1].contents[0],
                'MC_USD_Billion' : col[2].contents[0]}
            df1 = pd.DataFrame(data_dict, index = [0])
            df = pd.concat([df,df1], ignore_index=True)
    return df


def transform(df, csv_path):
    tl = df['MC_USD_Billion'].tolist()
    tl = [float(x.replace('\n','')) for x in tl]
    df['MC_USD_Billion'] = tl
    input = pd.read_csv(csv_path)
    exchange_rate = input.set_index('Currency').to_dict()['Rate']
    df['MC_GBP_Billion'] = [np.round(x*exchange_rate['GBP'],2) for x in df['MC_USD_Billion']]
    df['MC_EUR_Billion'] = [np.round(x*exchange_rate['EUR'],2) for x in df['MC_USD_Billion']]
    df['MC_INR_Billion'] = [np.round(x*exchange_rate['INR'],2) for x in df['MC_USD_Billion']]
    return df

def load_to_csv(df, output_path):
    df.to_csv(output_path)

def load_to_db(df, sql_connection, table_name):
    df.to_sql(table_name, sql_connection, if_exists='replace', index=False)

def run_query(query_statement, sql_connection):
    print(query_statement)
    query_output = pd.read_sql(query_statement, sql_connection)
    print(query_output)

#------------------------------------------------

URL = 'https://en.wikipedia.org/wiki/List_of_largest_banks'
table_attributes = ['Name','MC_USD_Billion']
csv_path = './exchange_rate.csv'
output_csv_path = './Largest_banks_data.csv'
table_name = 'Largest_Banks'


log_progress('Preliminaries complete. Initiating ETL process')

df = extract(URL,table_attributes)
#print(df)

log_progress('Data extraction complete. Initiating Transformation process')

df = transform(df,csv_path)
#print(df.to_string())
#print("quiz", df['MC_EUR_Billion'][4])
log_progress('Data transformation complete. Initiating loading process')


load_to_csv(df, output_csv_path)
log_progress('Data saved to CSV file')


sql_connection = sqlite3.connect('Banks.db')
log_progress('SQL Connection initiated.')
load_to_db(df, sql_connection, table_name)
log_progress('Data loaded to Database as table. Running the query')


query = f"SELECT * FROM {table_name}"
run_query(query, sql_connection)

query = f"SELECT AVG(MC_GBP_Billion) FROM {table_name}"
run_query(query, sql_connection)

query = f"SELECT Name FROM {table_name} LIMIT 5"
run_query(query, sql_connection)


log_progress('Process Complete')


sql_connection.close()
log_progress('Server Connection closed')