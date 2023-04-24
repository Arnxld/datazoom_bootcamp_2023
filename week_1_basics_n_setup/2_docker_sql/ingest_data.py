import os
import argparse # named cli arguments

import pandas as pd
from sqlalchemy import create_engine
from time import time

def main(params):
    user = params.user
    password = params.password
    host = params.host
    port = params.port
    db = params.db
    table_name = params.table_name
    url = params.url


    zip_csv_name = 'output.csv.gz'
    csv_name = 'output.csv'
    
    os.system(f"wget {url} -O {zip_csv_name}")
    os.system(f"gunzip {zip_csv_name}")

    engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{db}') # cria a conexao com o db


    df_iter = pd.read_csv(csv_name, iterator=True, chunksize=100000) # cria o iterator em cima dos dados

    df = next(df_iter) # pega o proximo chunk

    df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime) # muda o dado para datetime
    df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime) # muda o dado para datetime

    df.head(0).to_sql(con=engine, name=table_name, if_exists='replace') # cria a tabela

    df.to_sql(con=engine, name=table_name, if_exists='append') # faz a ingestão do primeiro chunk

    os.system("rm output.csv")
    
    while True: # ingestão dos chunks
        t_start = time()
        df = next(df_iter)
        
        df.tpep_pickup_datetime = pd.to_datetime(df.tpep_pickup_datetime)
        df.tpep_dropoff_datetime = pd.to_datetime(df.tpep_dropoff_datetime)
        
        df.to_sql(con=engine, name=table_name, if_exists='append')
        t_end = time()
        print(f'inserted another chunk... it took {t_end - t_start}')
    

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Ingest CSV data to Postgres")
    parser.add_argument('--user', help="username for postgres")
    parser.add_argument('--password', help="password for postgres")
    parser.add_argument('--host', help="host for postgres")
    parser.add_argument('--port', help="port for postgres")
    parser.add_argument('--db', help="database name for postgres")
    parser.add_argument('--table_name', help="table where we will write the resuls to")
    parser.add_argument('--url', help="url of the csv file")

    args = parser.parse_args()

    main(args)

