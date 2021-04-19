from pyspark.sql import SparkSession

from data_ingestion.config import job_parameters
from data_ingestion.ingestion import Ingestion

# ---------- Part III: Run Da Ting (for Part II, see data_ingestion/ingestion.py) ---------- #

spark = SparkSession \
    .builder \
    .appName("TWDU Germany Glue Data Ingestion") \
    .config("spark.some.config.option", "some-value") \
    .getOrCreate()

Ingestion(spark, job_parameters).run()