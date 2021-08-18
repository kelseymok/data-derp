from typing import Dict
from pyspark.sql import DataFrame, Column
import pyspark.sql.functions as F
from pyspark.sql.session import SparkSession
from pyspark.sql.types import *

# ---------- Part II: Business Logic (for Part I, see data_transformation/config.py) ---------- #

class Transformer:
    """Data Transformer Python Class"""

    def __init__(self, spark: SparkSession, parameters: Dict[str, str], boss_level: bool = True):
        self.spark = spark
        self.parameters = parameters
        self.boss_level = boss_level
        return

    @staticmethod
    def get_country_emissions(co2_df: DataFrame) -> DataFrame:
        """
        Topics: cast, select, alias

        Read EmissionsByCountry.parquet into a Spark DataFrame.
        Make sure that each Entity is a country.

        Your output Spark DataFrame's schema should be:
            - Year: integer
            - Country: string
            - TotalEmissions: float
            - PerCapitaEmissions: float
            - ShareOfGlobalEmissions: float
        """

        # You'll notice that there's an Entity called "World".
        # Since we're analyzing emissions of countries, let's discard "World"
        country_emissions = co2_df \
            .filter(F.col("Entity") != F.lit("World")) \
            .select(
                F.col("Year"),
                F.col("Entity").alias("Country"),
                F.col("Annual_CO2_emissions").cast(FloatType()).alias("TotalEmissions"),
                F.col("Per_capita_CO2_emissions").cast(FloatType()).alias("PerCapitaEmissions"),
                F.col("Share_of_global_CO2_emissions").cast(FloatType()).alias("ShareOfGlobalEmissions"),
            )
        return country_emissions

    @staticmethod # doesn't rely on self.spark nor self.parameters
    def aggregate_global_emissions(country_emissions: DataFrame) -> DataFrame:
        """
        Topics: aggregate functions, alias

        Aggregate the total CO2 emissions globally on an ANNUAL basis.
        Your output Spark DataFrame's schema should be:
            - Year: integer
            - TotalEmissions: float
        """
        global_emissions = country_emissions.groupBy("Year").agg(
            F.sum(F.col("TotalEmissions")).cast(FloatType()).alias("TotalEmissions")
        )
        return global_emissions

    @staticmethod
    def aggregate_global_temperatures(temperatures_global_df: DataFrame) -> DataFrame:
        """
        Topics: aggregate functions, alias

        Aggregate temperature measurements globally on an ANNUAL basis.
        Think carefully about the appropriate aggregation functions to use.
        For this project, you can just ignore any 'Uncertainty' columns.
        Your output Spark DataFrame's schema should be:
            - Year: integer
            - LandAverageTemperature: float
            - LandMaxTemperature: float
            - LandMinTemperature: float
            - LandAndOceanAverageTemperature: float
        """
        temps_global_df = temperatures_global_df.withColumn("Year", F.year(F.col("Date")))

        global_temperatures = temps_global_df.groupBy("Year").agg(
            # TODO: Exercise
        )
        return global_temperatures

    @staticmethod # doesn't rely on self.spark nor self.parameters
    def join_global_emissions_temperatures(
        global_emissions: DataFrame, 
        global_temperatures: DataFrame
        ) -> DataFrame:
        """
        Topics: joins

        Perform an INNER JOIN between the results of
            1. aggregate_global_emissions
            2. aggregate_global_temperatures
        Your output Spark DataFrame's schema should be:
            - Year: integer
            - TotalEmissions: float
            - LandAverageTemperature: float
            - LandMaxTemperature: float
            - LandMinTemperature: float
            - LandAndOceanAverageTemperature: float
        """
        global_emissions_temperatures = global_emissions.join(
            # TODO: Exercise
        ) 
        return global_emissions_temperatures

    @staticmethod # doesn't rely on self.spark nor self.parameters
    def fix_country(col: Column) -> Column:
        """
        Use built-in Spark functions to clean-up the "Country" column
        e.g. "   cAnAdA " -> "Canada"
        Don't forget about those annoying leading/trailing spaces.
        """
        fixed_country = NotImplemented # TODO: Exercise
        if fixed_country is NotImplemented:
            raise NotImplemented("DO YOUR HOMEWORK OR NO TV")
        return fixed_country

    @staticmethod # doesn't rely on self.spark nor self.parameters    
    def remove_lenny_face(temperature: str) -> str:
        """
        HINT: only temperature entries with Lenny's face are valid measurements
        There are multiple ways to tackle this: udf, pandas_udf, regexp_extract, regexp_replace, etc.
        Normally, we'd recommend a pandas_udf as it's a nice transferrable skill with good performance.
        However, to keep this job simple, let's use a standard Python function.
        We will later convert this function (remove_lenny_face) to a UDF in the aggregate_country_temperatures function.

        The point is to demonstrate that you can write arbitrary Python logic as a UDF 
        if Spark doesn't have the built-in function you need.
        """
        fixed_temperature_string = NotImplemented # TODO: Exercise
        if fixed_temperature_string is NotImplemented:
            raise NotImplemented("DO YOUR HOMEWORK OR NO CHOCOLATE")
        return fixed_temperature_string

    def aggregate_country_temperatures(self, temperatures_country_df: DataFrame) -> DataFrame:
        """
        Topics: casting, udf/pandas_udf, aggregation functions

        Aggregate temperature measurements per country on an ANNUAL basis.
        INVESTIGATE the data to look for any data quality issues
        Think carefully about:
            - any necessary cleaning (WARNING: don't assume Spark can intelligently read/cast everything)
            - the appropriate aggregation function to use
        For this project, you can just ignore any 'Uncertainty' columns.
        Your output Spark DataFrame's schema should be:
            - Year: integer
            - Country: string
            - AverageTemperature: float
        """
        # Register your function as a UDF
        fix_temperature_udf = F.udf(self.remove_lenny_face, returnType=StringType())
        temperature_expr = fix_temperature_udf(F.col("AverageTemperature")).cast(FloatType())

        # Unlike the Global Temperatures dataset...Spark couldn't automatically parse the "Date" column as a timestamp
        # You'll have to find a built-in function to perform the conversion then extract the year
        year_expr = F.year(F.to_timestamp(F.col("Date"), format="MM-dd-yyyy")) # TODO: Exercise
        country_expr = self.fix_country(F.col("Country")) # TODO: Exercise

        country_temperatures = NotImplemented # TODO: Exercise
        if country_temperatures is NotImplemented:
            raise NotImplemented("DO YOUR HOMEWORK OR NO ICE CREAM")
        return country_temperatures

    @staticmethod # doesn't rely on self.spark nor self.parameters
    def join_country_emissions_temperatures(
        country_emissions: DataFrame,
        country_temperatures: DataFrame) -> DataFrame:
        """
        Topics: joins

        Perform an INNER JOIN between the results of:
            1. get_country_emissions
            2. aggregate_country_temperatures
        Your output Spark DataFrame's schema should be:
            - Year: integer
            - Country: string
            - TotalEmissions: float
            - PerCapitaEmissions: float
            - ShareOfGlobalEmissions: float
            - AverageTemperature: float
        """
        # HINT: don't forget a slight modification compared to the join_global_emissions_temperatures function
        # In the real world, you should always make sure that the country names have been standardized.
        # However, for our exercise, just assume that a no-match is truly no-match.
        country_emissions_temperatures = country_emissions.join(
            # TODO: Exercise
        )
        return country_emissions_temperatures

    @staticmethod # doesn't rely on self.spark nor self.parameters
    def reshape_europe_big_three_emissions(country_emissions: DataFrame) -> DataFrame:
        """
        Topics: filter, pivot (with distinct values hinting) 

        Using the result of get_country_emissions, filter for 1900 onwards only.
        Next, reshape the data to satisfy the requirements below.

        Your output Spark DataFrame's schema should be:
            - Year: integer
            - France_TotalEmissions: float
            - France_PerCapitaEmissions: float
            - Germany_TotalEmissions: float
            - Germany_PerCapitaEmissions: float
            - UnitedKingdom_TotalEmissions: float
            - UnitedKingdom_PerCapitaEmissions: float
        """
        # TODO: exercise
        modern_era_df = country_emissions.filter(F.col("Year") >= F.lit(1900))
        europe_big_three_emissions = NotImplemented
        if europe_big_three_emissions is NotImplemented:
            raise NotImplemented("DO YOUR HOMEWORK OR NO PIZZA")

        # You might've noticed that "United Kingdom" has a space. 
        # If you recall, spaces are not permitted in Apache Parquet column names. Let's address that:
        friendly_columns = [F.col(x).alias(x.replace(" ", "")) for x in europe_big_three_emissions.columns]
        europe_big_three_emissions = europe_big_three_emissions.select(friendly_columns)
        return europe_big_three_emissions

    @staticmethod # doesn't rely on self.spark nor self.parameters
    def boss_battle(country_emissions: DataFrame) -> DataFrame:
        """
        Topics: when (switch statements), udf/pandas_udf, Window functions, coalesce (filling nulls with a priority order)

        The CO2 data provider for Australia and New Zealand informs you that there's a massive bug in their TotalEmissions estimations for LEAP YEARS only.
        As a result, your team will have to produce an edited dataset for Australia and New Zealand only.
        Using the result of get_country_emissions, disregard the TotalEmissions estimates for leap years, then replace them using the following PRIORITY:
            1. nearest non-null value from the past 3 years (i.e. 'forward fill')
            2. nearest non-null value from the future 3 years (i.e. 'backward fill')
            3. nullify the value (i.e. DO NOT accept the original TotalEmissions value for any leap year under any circumstance)
        Recap:
            - DISCARD all rows for countries other than Australia or New Zealand
            - KEEP rows from all years (including non-leap years) for Australia or New Zealand
            - KEEP only the following columns: Year, Country, and TotalEmissions
            * DEFINITION of past 3 years = [2017, 2018, 2019] if the year is 2020
            * DEFINITION of future 3 years = [2021, 2022, 2023] if the year is 2020

        Your output Spark DataFrame's schema should be:
            - Year: integer
            - Country: string
            - TotalEmissions: float
        """
        oceania_emissions = country_emissions.filter(F.col("Country").isin(["Australia", "New Zealand"]))

        # HINT: Python UDFs allow you to import external libraries
        def check_leap(year: int) -> bool:
            leap_bool = NotImplemented # TODO: Exercise
            if leap_bool is NotImplemented:
                raise NotImplemented("DO YOUR HOMEWORK OR NO CAKE")
            return leap_bool

        leap_year_udf = F.udf(check_leap, returnType=BooleanType())
        is_leap_year = leap_year_udf(F.col("Year"))

        # HINT: Carefully look up the Spark Window semantics
        # (partitionBy, orderBy, rowsBetween, rangeBetween)
        # Look carefully for the right Window functions to apply as well.
        w_past = NotImplemented # TODO: should be a Window (from pyspark.sql.window import Window)
        w_future = NotImplemented # TODO: should be a Window (from pyspark.sql.window import Window)
        nearest_before = NotImplemented # TODO: should be a Column Expression
        nearest_after = NotImplemented # TODO: should be a Column Expression
        
        if any(x is NotImplemented for x in [w_past, w_future, nearest_before, nearest_after]):
            raise NotImplemented("DO YOUR HOMEWORK OR NO CHIPS")

        # HINT: how do you choose the first column that is non-null in Spark (or SQL)? 
        emissions_prioritized = NotImplemented # TODO: should be a Column Expression (please read the HINT above)
        # HINT: how do you do perform case-switch statements in Spark?
        emissions_case = NotImplemented # TODO: should be a Column Expression (please read the HINT above)
        if any(x is NotImplemented for x in [emissions_prioritized, emissions_case]):
            raise NotImplemented("DO YOUR HOMEWORK OR NO NACHOS")
        
        emissions_expr = emissions_case.cast(FloatType())
        oceania_emissions_edited = oceania_emissions.select(
            "Year",
            "Country",
            emissions_expr.alias("TotalEmissions")
        )
        return oceania_emissions_edited

    def run(self):
        """
        BEFORE writing out any Spark DataFrame to S3:
            - coalesce to 1 partition
            - orderBy("Year") 
        This is just for convenience in our testing functions :)
        """
        # Setup: read all input DataFrames
        co2_input_df: DataFrame = self.spark.read.format("parquet").load(self.parameters["co2_input_path"])
        temperatures_global_input_df: DataFrame = self.spark.read.format("parquet").load(self.parameters["temperatures_global_input_path"])
        temperatures_country_input_df: DataFrame = self.spark.read.format("parquet").load(self.parameters["temperatures_country_input_path"])

        # Task 1:
        country_emissions: DataFrame = self.get_country_emissions(co2_input_df)
        global_emissions: DataFrame = self.aggregate_global_emissions(country_emissions)
        global_temperatures: DataFrame = self.aggregate_global_temperatures(temperatures_global_input_df)
        global_emissions_temperatures: DataFrame = self.join_global_emissions_temperatures(
            global_emissions, 
            global_temperatures
            )
        global_emissions_temperatures.coalesce(1).orderBy("Year") \
            .write.format("parquet").mode("overwrite") \
            .save(self.parameters["co2_temperatures_global_output_path"])

        # Task 2:
        country_temperatures: DataFrame = self.aggregate_country_temperatures(temperatures_country_input_df)
        country_emissions_temperatures: DataFrame = self.join_country_emissions_temperatures(
            country_emissions, 
            country_temperatures
        )
        country_emissions_temperatures.coalesce(1).orderBy("Year") \
            .write.format("parquet").mode("overwrite") \
            .save(self.parameters["co2_temperatures_country_output_path"])

        # Task 3:
        europe_big_three_emissions: DataFrame = self.reshape_europe_big_three_emissions(country_emissions)
        europe_big_three_emissions.coalesce(1).orderBy("Year") \
            .write.format("parquet").mode("overwrite") \
            .save(self.parameters["europe_big_3_co2_output_path"])

        # Task 4: 
        oceania_emissions_edited = self.boss_battle(country_emissions)
        oceania_emissions_edited.coalesce(1).orderBy("Year") \
            .write.format("parquet").mode("overwrite") \
            .save(self.parameters["co2_oceania_output_path"])

        # REVIEW: knowing that all Spark transformations are lazy and always get recomputed,
        # do you see any opportunities for improvement in performance?
        return
