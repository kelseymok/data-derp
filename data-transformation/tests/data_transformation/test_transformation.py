import pytest
import sys
import os

from shutil import rmtree
from pytest_mock.plugin import MockerFixture
from test_utils.pyspark import TestPySpark

from typing import List, Union

import pyspark.sql.functions as F
from pyspark.sql.types import *

import pandas as pd
import numpy as np
from datetime import datetime

from data_transformation.transformation import Transformer
from debugger import debug
from transformation_expected import get_expected_metadata

class TestTransformation(TestPySpark):

    @classmethod
    def setup_class(cls): # runs before each and every test
        cls.spark = cls.start_spark()
        root_dir = os.path.dirname(os.path.realpath(__file__)).split("/data-transformation/")[0]
        cls.parameters = {
        "co2_input_path":                  f"{root_dir}/datasets/transformation/inputs/EmissionsByCountry.parquet/",
        "temperatures_global_input_path":  f"{root_dir}/datasets/transformation/inputs/GlobalTemperatures.parquet/",
        "temperatures_country_input_path": f"{root_dir}/datasets/transformation/inputs/TemperaturesByCountry.parquet/",

        "co2_temperatures_global_output_path":  f"{root_dir}/data-transformation/tmp/test/outputs/GlobalEmissionsVsTemperatures.parquet/",
        "co2_temperatures_country_output_path": f"{root_dir}/data-transformation/tmp/test/outputs/CountryEmissionsVsTemperatures.parquet/",
        "europe_big_3_co2_output_path":         f"{root_dir}/data-transformation/tmp/test/outputs/EuropeBigThreeEmissions.parquet/",
        "co2_oceania_output_path":              f"{root_dir}/data-transformation/tmp/test/outputs/OceaniaEmissionsEdited.parquet/",
        }
        cls.transformer = Transformer(cls.spark, cls.parameters)
        return

    @classmethod
    def teardown_class(cls):
        cls.stop_spark()
        output_paths = cls.parameters.values()
        for path in output_paths:
            if ("/tmp/" in path) and os.path.exists(path):
                rmtree(path.rsplit("/", 1)[0])

    @staticmethod
    def prepare_frame(
        df: pd.DataFrame, column_order: List[str] = None, sort_keys: List[str] = None,
        ascending: Union[bool, List[bool]] = True, reset_index: bool = True):
        """Prepare Pandas DataFrame for equality check"""
        if column_order is not None: df = df.loc[:, column_order]
        if sort_keys is not None: df = df.sort_values(sort_keys, ascending=ascending)
        if reset_index: df = df.reset_index(drop=True)
        return df

    def test_get_country_emissions(self):
        """Tests the get_country_emissions method"""
        input_pandas = pd.DataFrame({
            "Year": [1999, 2000, 2001, 2020, 2021],
            "Entity" : ["World", "World", "World", "Fiji", "Argentina"],
            "Annual_CO2_emissions": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Per_capita_CO2_emissions": [1.0, 2.0, 3.0, 4.0, 5.0],
            "Share_of_global_CO2_emissions": [0.5, 0.5, 0.5, 0.5, 0.5]
        })
        input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Entity", StringType(), True),
            StructField("Annual_CO2_emissions", FloatType(), True),
            StructField("Per_capita_CO2_emissions", FloatType(), True),
            StructField("Share_of_global_CO2_emissions", FloatType(), True),
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = ["Year", "Country", "TotalEmissions", "PerCapitaEmissions", "ShareOfGlobalEmissions"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([2020, 2021], dtype=np.dtype("int32")),
            "Country" : pd.Series(["Fiji", "Argentina"], dtype=str),
            "TotalEmissions": pd.Series([4.0, 5.0], dtype=np.dtype("float32")),
            "PerCapitaEmissions": pd.Series([4.0, 5.0], dtype=np.dtype("float32")),
            "ShareOfGlobalEmissions": pd.Series([0.5, 0.5], dtype=np.dtype("float32"))
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        output_df = self.transformer.get_country_emissions(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert "World" not in output_pandas["Country"].str.title().values
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_aggregate_global_emissions(self):
        """Tests the aggregate_global_emissions method"""
        input_pandas = pd.DataFrame({
            "Year": [1999, 1999, 1999, 2020, 2020, 2021],
            "Country" : ["Tuvalu", "Lichtenstein", "Togo", "Singapore", "Fiji", "Argentina"],
            "TotalEmissions": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            "PerCapitaEmissions": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            "ShareOfGlobalEmissions": [0.33, 0.33, 0.33, 0.5, 0.5, 0.5]
        })
        input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Country", StringType(), True),
            StructField("TotalEmissions", FloatType(), True),
            StructField("PerCapitaEmissions", FloatType(), True),
            StructField("ShareOfGlobalEmissions", FloatType(), True),
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = ["Year", "TotalEmissions"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020, 2021], dtype=np.dtype("int32")),
            "TotalEmissions": pd.Series([6.0, 9.0, 6.0], dtype=np.dtype("float32"))
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        output_df = self.transformer.aggregate_global_emissions(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_aggregate_global_temperatures(self):
        """Tests the aggregate_global_temperatures method"""
        input_pandas = pd.DataFrame({
            "Date": [datetime(1999, 11, 1), datetime(1999, 12, 1), datetime(2020, 1, 1), datetime(2020, 2, 1), datetime(2020, 3, 1)],
            "LandAverageTemperature": [1.0, 0.0, 1.0, 2.0, 3.0],
            "LandMaxTemperature": [6.0, 9.0, 6.9, 4.20, 6.9420],
            "LandMinTemperature": [-6.0, -9.0, -6.9, -4.20, -6.9420],
            "LandAndOceanAverageTemperature": [1.0, 0.0, 1.0, 2.0, 3.0]
        })
        input_schema = StructType([
            StructField("Date", TimestampType(), True),
            StructField("LandAverageTemperature", FloatType(), True),
            StructField("LandMaxTemperature", FloatType(), True),
            StructField("LandMinTemperature", FloatType(), True),
            StructField("LandAndOceanAverageTemperature", FloatType(), True),
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = ["Year", "LandAverageTemperature", "LandMaxTemperature", "LandMinTemperature", "LandAndOceanAverageTemperature"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020], dtype=np.dtype("int32")),
            "LandAverageTemperature": pd.Series([0.5, 2.0], dtype=np.dtype("float32")),
            "LandMaxTemperature": pd.Series([9.0, 6.9420], dtype=np.dtype("float32")),
            "LandMinTemperature": pd.Series([-9.0, -6.9420], dtype=np.dtype("float32")),
            "LandAndOceanAverageTemperature": pd.Series([0.5, 2.0], dtype=np.dtype("float32")),
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        output_df = self.transformer.aggregate_global_temperatures(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_join_global_emissions_temperatures(self):
        """Tests the join_global_emissions_temperatures method"""
        emissions_input_pandas = pd.DataFrame({
            "Year": [1999, 2020, 2021],
            "TotalEmissions": [6.0, 9.0, 6.0]
        })
        emissions_input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("TotalEmissions", FloatType(), True)
        ])
        emissions_input_df = self.spark.createDataFrame(emissions_input_pandas, emissions_input_schema)

        temperatures_input_pandas = pd.DataFrame({
            "Year": [1999, 2020],
            "LandAverageTemperature": [0.5, 2.0],
            "LandMaxTemperature": [9.0, 6.9420],
            "LandMinTemperature": [-9.0, -6.9420],
            "LandAndOceanAverageTemperature": [0.5, 2.0],
        })
        temperatures_input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("LandAverageTemperature", FloatType(), True),
            StructField("LandMaxTemperature", FloatType(), True),
            StructField("LandMinTemperature", FloatType(), True),
            StructField("LandAndOceanAverageTemperature", FloatType(), True),
        ])
        temperatures_input_df = self.spark.createDataFrame(temperatures_input_pandas, temperatures_input_schema)

        expected_columns = ["Year", "TotalEmissions", "LandAverageTemperature", "LandMaxTemperature", "LandMinTemperature", "LandAndOceanAverageTemperature"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020], dtype=np.dtype("int32")),
            "TotalEmissions": pd.Series([6.0, 9.0], dtype=np.dtype("float32")),
            "LandAverageTemperature": pd.Series([0.5, 2.0], dtype=np.dtype("float32")),
            "LandMaxTemperature": pd.Series([9.0, 6.9420], dtype=np.dtype("float32")),
            "LandMinTemperature": pd.Series([-9.0, -6.9420], dtype=np.dtype("float32")),
            "LandAndOceanAverageTemperature": pd.Series([0.5, 2.0], dtype=np.dtype("float32")),
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        output_df = self.transformer.join_global_emissions_temperatures(emissions_input_df, temperatures_input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_fix_country(self):
        """Tests the fix_country method"""
        original = pd.Series(["  gErMaNy ", "   uNiTeD sTaTeS    "])
        spark_df = self.spark.createDataFrame(pd.DataFrame({"Country": original}))
        spark_df = spark_df.withColumn("Country", self.transformer.fix_country(F.col("Country")))
        fixed = spark_df.toPandas()
        try:
            result = sorted(fixed["Country"])
            assert result == ["Germany", "United States"]
        except Exception as e:
            raise type(e)(''.join(debug(original))) from e

    def test_remove_lenny_face(self):
        """Tests the remove_lenny_face method.

        Objective: Convert an incoming string into a format that can be casted to a FloatType by Spark.
        Spark is smart enough to convert "69.420" to 69.420 but <69.420> will be casted to a null.
        To keep the exercise simple (no regex required), you'll only need to handle the Lenny face.
        """
        original = pd.Series(["( ͡° ͜ʖ ͡°)4.384( ͡° ͜ʖ ͡°)", "-", "?", "#", "( ͡° ͜ʖ ͡°)1.53( ͡° ͜ʖ ͡°)"])
        try:
            result = original.map(self.transformer.remove_lenny_face)
            assert result.to_list() == ["4.384", "-", "?", "#", "1.53"] # make valid floats parsable
            spark_df = self.spark.createDataFrame(pd.DataFrame({"lol": result}))
            spark_df = spark_df.withColumn("lmao", F.col("lol").cast(FloatType())) # automatic casting with spark
            assert spark_df.filter(F.col("lmao").isNull()).count() == 3
            assert spark_df.filter(F.col("lmao").isNotNull()).count() == 2
        except Exception as e:
            raise type(e)(''.join(debug(original))) from e

    def test_aggregate_country_temperatures(self):
        """Tests the aggregate_country_temperatures method"""
        input_pandas = pd.DataFrame({
            "Date": ["11-30-1999", "12-31-1999", "01-01-2020", "02-01-2020", "03-01-2020"],
            "Country":  [" bRaZiL  ", "   BrAzIl ", "japaN", "OMAN", "oman"],
            "AverageTemperature": ["( ͡° ͜ʖ ͡°)1.0( ͡° ͜ʖ ͡°)", "( ͡° ͜ʖ ͡°)0.0( ͡° ͜ʖ ͡°)", "-", "?", "( ͡° ͜ʖ ͡°)3.0( ͡° ͜ʖ ͡°)"]
        })
        input_schema = StructType([
            StructField("Date", StringType(), True),
            StructField("Country", StringType(), True),
            StructField("AverageTemperature", StringType(), True)
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = ["Year", "Country", "AverageTemperature"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020, 2020], dtype=np.dtype("int32")),
            "Country": pd.Series(["Brazil", "Japan", "Oman"], dtype=np.dtype("O")),
            "AverageTemperature": pd.Series([0.5, np.nan, 3.0], dtype=np.dtype("float32"))
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        output_df = self.transformer.aggregate_country_temperatures(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_join_country_emissions_temperatures(self):
        """Tests the join_country_emissions_temperatures method"""
        emissions_input_pandas = pd.DataFrame({
            "Year": [1999, 2000, 2001, 2020, 2021],
            "Country" : ["Brazil", "Tunisia", "Russia", "Oman", "Indonesia"],
            "TotalEmissions": [1.0, 2.0, 3.0, 4.0, 5.0],
            "PerCapitaEmissions": [0.1, 0.2, 0.3, 0.4, 0.5],
            "ShareOfGlobalEmissions": [0.1, 0.2, 0.3, 0.4, 0.5]
        })
        emissions_input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Country", StringType(), True),
            StructField("TotalEmissions", FloatType(), True),
            StructField("PerCapitaEmissions", FloatType(), True),
            StructField("ShareOfGlobalEmissions", FloatType(), True)
        ])
        emissions_input_df = self.spark.createDataFrame(emissions_input_pandas, emissions_input_schema)

        temperatures_input_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020, 2020], dtype=np.dtype("int32")),
            "Country": pd.Series(["Brazil", "Japan", "Oman"], dtype=np.dtype("O")),
            "AverageTemperature": pd.Series([0.5, np.nan, 3.0], dtype=np.dtype("float32"))
        })
        temperatures_input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Country", StringType(), True),
            StructField("AverageTemperature", FloatType(), True)
        ])
        temperatures_input_df = self.spark.createDataFrame(temperatures_input_pandas, temperatures_input_schema)

        expected_columns = ["Year", "Country", "TotalEmissions", "PerCapitaEmissions", "ShareOfGlobalEmissions", "AverageTemperature"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020], dtype=np.dtype("int32")),
            "Country": pd.Series(["Brazil", "Oman"], dtype=np.dtype("O")),
            "TotalEmissions": pd.Series([1.0, 4.0], dtype=np.dtype("float32")),
            "PerCapitaEmissions": pd.Series([0.1, 0.4], dtype=np.dtype("float32")),
            "ShareOfGlobalEmissions": pd.Series([0.1, 0.4], dtype=np.dtype("float32")),
            "AverageTemperature": pd.Series([0.5, 3.0], dtype=np.dtype("float32")),
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        output_df = self.transformer.join_country_emissions_temperatures(emissions_input_df, temperatures_input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_reshape_europe_big_three_emissions(self):
        """Tests the reshape_europe_big_three_emissions method"""
        input_pandas = pd.DataFrame({
                    "Year": [1999, 1999, 1999, 2020, 2020, 2021],
                    "Country" : ["France", "Germany", "United Kingdom", "France", "Germany", "United Kingdom"],
                    "TotalEmissions": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
                    "PerCapitaEmissions": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
                    "ShareOfGlobalEmissions": [0.33, 0.33, 0.33, 0.5, 0.5, 0.5]
                })
        input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Country", StringType(), True),
            StructField("TotalEmissions", FloatType(), True),
            StructField("PerCapitaEmissions", FloatType(), True),
            StructField("ShareOfGlobalEmissions", FloatType(), True),
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = [
            "Year",
            "France_TotalEmissions", "France_PerCapitaEmissions",
            "Germany_TotalEmissions", "Germany_PerCapitaEmissions",
            "UnitedKingdom_TotalEmissions", "UnitedKingdom_PerCapitaEmissions",
        ]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1999, 2020, 2021], dtype=np.dtype("int32")),
            "France_TotalEmissions": pd.Series([1.0, 4.0, np.nan], dtype=np.dtype("float32")),
            "France_PerCapitaEmissions": pd.Series([0.1, 0.4, np.nan], dtype=np.dtype("float32")),
            "Germany_TotalEmissions": pd.Series([2.0, 5.0, np.nan], dtype=np.dtype("float32")),
            "Germany_PerCapitaEmissions": pd.Series([0.2, 0.5, np.nan], dtype=np.dtype("float32")),
            "UnitedKingdom_TotalEmissions": pd.Series([3.0, np.nan, 6.0], dtype=np.dtype("float32")),
            "UnitedKingdom_PerCapitaEmissions": pd.Series([0.3, np.nan, 0.6], dtype=np.dtype("float32"))
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        output_df = self.transformer.reshape_europe_big_three_emissions(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_boss_battle(self):
        """Tests the boss_battle method"""
        input_pandas = pd.DataFrame({
            "Year": [1997, 1998, 2000, 2001, 2016, 2020, 2022, 2023, 2024],
            "Country" : [
                "United States",
                "Australia", "Australia", "Australia",
                "New Zealand", "New Zealand", "New Zealand", "New Zealand", "New Zealand"],
            "TotalEmissions": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.5, 7.0, 8.0],
            "PerCapitaEmissions": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.8],
            "ShareOfGlobalEmissions": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.8]
        })
        input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Country", StringType(), True),
            StructField("TotalEmissions", FloatType(), True),
            StructField("PerCapitaEmissions", FloatType(), True),
            StructField("ShareOfGlobalEmissions", FloatType(), True)
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = ["Year", "Country", "TotalEmissions"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([1998, 2000, 2001, 2016, 2020, 2022, 2023, 2024], dtype=np.dtype("int32")),
            "Country": pd.Series([
                "Australia", "Australia", "Australia",
                "New Zealand", "New Zealand", "New Zealand", "New Zealand", "New Zealand"], dtype=np.dtype("O")),
            "TotalEmissions": pd.Series([2.0, 2.0, 4.0, np.nan, 6.5, 6.5, 7.0, 7.0], dtype=np.dtype("float32"))
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        output_df = self.transformer.boss_battle(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert sorted(output_pandas["Country"].unique()) == sorted(["Australia", "New Zealand"])
        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_boss_battle_the_revenge(self):
        """Tests the boss_battle method"""
        input_pandas = pd.DataFrame({
            "Year": [1997, 2019, 2020, 2022, 2016, 2020, 2022, 2023, 2024],
            "Country" : [
                "United States",
                "Australia", "Australia", "Australia",
                "New Zealand", "New Zealand", "New Zealand", "New Zealand", "New Zealand"],
            "TotalEmissions": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 6.5, 7.0, 8.0],
            "PerCapitaEmissions": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.8],
            "ShareOfGlobalEmissions": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.7, 0.8]
        })
        input_schema = StructType([
            StructField("Year", IntegerType(), True),
            StructField("Country", StringType(), True),
            StructField("TotalEmissions", FloatType(), True),
            StructField("PerCapitaEmissions", FloatType(), True),
            StructField("ShareOfGlobalEmissions", FloatType(), True)
        ])
        input_df = self.spark.createDataFrame(input_pandas, input_schema)

        expected_columns = ["Year", "Country", "TotalEmissions"]
        expected_pandas = pd.DataFrame({
            "Year": pd.Series([2016, 2019, 2020, 2020, 2022, 2022, 2023, 2024], dtype=np.dtype("int32")),
            "Country": pd.Series([
                "New Zealand", "Australia", "Australia",
                "New Zealand", "Australia", "New Zealand", "New Zealand", "New Zealand"], dtype=np.dtype("O")),
            "TotalEmissions": pd.Series([np.nan, 2.0, 2.0, 6.5, 4.0, 6.5, 7.0, 7.0], dtype=np.dtype("float32"))
        })
        expected_pandas = self.prepare_frame(
            expected_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        output_df = self.transformer.boss_battle(input_df)
        output_pandas: pd.DataFrame = output_df.toPandas()
        output_pandas = self.prepare_frame(
            output_pandas,
            column_order=expected_columns, # ensure column order
            sort_keys=["Year", "Country"], # ensure row order
        )
        print("Schemas:")
        print(expected_pandas.dtypes)
        print(output_pandas.dtypes)
        print("Contents:")
        print(expected_pandas)
        print(output_pandas)

        assert sorted(output_pandas["Country"].unique()) == sorted(["Australia", "New Zealand"])
        assert list(output_pandas.columns) == expected_columns # check column names and order
        assert output_pandas.equals(expected_pandas) # check contents and data types

    def test_run(self, mocker: MockerFixture):
        """High level job test: count + schema checks but nothing more granular"""

        # Optional - if mocking is needed:
        # mock_object = mocker.Mock()
        # mock_object.some_property.some_method(some_argument).another_method.return_value = ...

        # Run the job and check for _SUCCESS files for each partition
        self.transformer.run()

        output_path_keys = [
            "co2_temperatures_global_output_path",
            "co2_temperatures_country_output_path",
            "europe_big_3_co2_output_path",
            "co2_oceania_output_path"
            ]
        output_path_values = [self.parameters[k] for k in output_path_keys]
        expected_metadata_dict = get_expected_metadata()
        expected_metadata = [expected_metadata_dict[k.replace("_path", "")] for k in output_path_keys]

        for (path, expected) in list(zip(output_path_values, expected_metadata)):
            files = os.listdir(path)
            snappy_parquet_files = [x for x in files if x.endswith(".snappy.parquet")]
            # For this exercise, we require you to control each table's partitioning to 1 parquet partition
            assert (True if len(snappy_parquet_files) == 1 else False)
            assert (True if "_SUCCESS" in files else False)

            # Check count and schema - this covers most of pyspark-test's (https://pypi.org/project/pyspark-test/) functionality already
            # No need for a full equality check (it collects everything into the driver's memory - too time/memory consuming)
            df = self.spark.read.parquet(path)
            assert df.count() == expected["count"]
            assert df.schema == expected["schema"]

if __name__ == '__main__':
    pytest.main(sys.argv)
