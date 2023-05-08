-- Creating external table referring to gcs path
CREATE OR REPLACE EXTERNAL TABLE `taxi_rides_ny.external_yellow_tripdata`
OPTIONS (
  format = 'PARQUET',
  uris = ['gs://prefect-zoomcamp-week2/data/yellow/yellow_tripdata_2021-*.parquet']
);

-- Check yello trip data
SELECT * FROM taxi_rides_ny.external_yellow_tripdata limit 10;

-- Create a non partitioned table from external table
CREATE OR REPLACE TABLE taxi_rides_ny.yellow_tripdata_non_partitioned AS
SELECT * FROM taxi_rides_ny.external_yellow_tripdata;


-- Create a partitioned table from external table
CREATE OR REPLACE TABLE taxi_rides_ny.yellow_tripdata_partitioned
PARTITION BY
  DATE(tpep_pickup_datetime) AS
SELECT * FROM taxi_rides_ny.external_yellow_tripdata;

-- Impact of partition
-- Scanning 1.6GB of data
SELECT DISTINCT(VendorID)
FROM taxi_rides_ny.yellow_tripdata_non_partitoned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-01-30';

-- Scanning ~106 MB of DATA
SELECT DISTINCT(VendorID)
FROM taxi_rides_ny.yellow_tripdata_partitoned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-01-30';

-- Let's look into the partitons
SELECT table_name, partition_id, total_rows
FROM `nytaxi.INFORMATION_SCHEMA.PARTITIONS`
WHERE table_name = 'yellow_tripdata_partitoned'
ORDER BY total_rows DESC;

-- Creating a partition and cluster table
CREATE OR REPLACE TABLE taxi_rides_ny.yellow_tripdata_partitoned_clustered
PARTITION BY DATE(tpep_pickup_datetime)
CLUSTER BY VendorID AS
SELECT * FROM taxi_rides_ny.external_yellow_tripdata;

-- Query scans 1.1 GB
SELECT count(*) as trips
FROM taxi_rides_ny.yellow_tripdata_partitoned
WHERE DATE(tpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-03-31'
  AND VendorID=1;

-- Query scans 864.5 MB
SELECT count(*) as trips
FROM taxi_rides_ny.yellow_tripdata_partitoned_clustered
WHERE DATE(tpep_pickup_datetime) BETWEEN '2021-01-01' AND '2021-03-31'
  AND VendorID=1;