from pathlib import Path
import pandas as pd
from prefect import flow, task
from prefect_gcp.cloud_storage import GcsBucket
from prefect.tasks import task_input_hash
from datetime import timedelta


@task(retries=3, cache_key_fn=task_input_hash, cache_expiration=timedelta(days=1))
def fetch(dataset_url: str) -> pd.DataFrame:
    """Read taxi data from web into pandas DataFrame"""

    df = pd.read_csv(dataset_url)
    return df

@task(log_prints=True)
def clean(df= pd.DataFrame) -> pd.DataFrame:
    """Fix dtype issues"""
    df['tpep_pickup_datetime'] = pd.to_datetime(df['tpep_pickup_datetime'])
    df['tpep_dropoff_datetime'] = pd.to_datetime(df['tpep_dropoff_datetime'])

    print(df.head(2))
    print(f"columns: {df.dtypes}")
    print(f"rows: {len(df)}")

    return df

@task(log_prints=True)
def write_local(df: pd.DataFrame, color: str, dataset_file: str) -> Path:
    """Write DataFrame out as parquet file"""
    # path = Path(f"/home/pedro/data-engineering-zoomcamp/week_2_workflow_orchestration/data/{color}/{dataset_file}.parquet")
    #path = Path(f"../../data/{color}/{dataset_file}.parquet")

    #path fix according to Zoomcamp FAQ https://docs.google.com/document/d/19bnYs80DwuUimHM65UV3sylsCn2j1vziPOwzBwQrebw/edit#
    path = Path(f"../../data/{color}/{dataset_file}.parquet")

    if not path.parent.is_dir():
        path.parent.mkdir(parents=True)

    df.to_parquet(path, compression="gzip")
    print(path)
    return path
    

@task(log_prints=True)
def write_gcs(path: Path, color: str) -> None:
    """Upload local parquet file to GCS"""

    # linha devido a mudança para o caminho da minha maquina
    file_name = str(path).split("/")[-1]

    gcs_block = GcsBucket.load("zoomcamp-gcs")

    gcs_block.upload_from_path(
        from_path=path,
        #to_path=path
        to_path=f"data/{color}/{file_name}"
    )

    return


# subflow
@flow()
def etl_web_to_gcs(color, year, month) -> None:
    """MAIN ETL FUNCTION"""
    dataset_file = f"{color}_tripdata_{year}-{month:02}"
    dataset_url = f"https://github.com/DataTalksClub/nyc-tlc-data/releases/download/{color}/{dataset_file}.csv.gz"

    df = fetch(dataset_url)
    df_clean = clean(df)
    path = write_local(df_clean, color, dataset_file)
    write_gcs(path, color)

# flow to trigger one subflow for each month
@flow()
def etl_parent_flow(
    months: list[int] = [1, 2],
    year: int = 2021,
    color: str = 'yellow'
):
    for month in months:
        etl_web_to_gcs(color, year, month)


if __name__ == '__main__':
    color = 'yellow'
    months = [1, 2, 3]
    year = 2021
    etl_parent_flow(months, year, color)