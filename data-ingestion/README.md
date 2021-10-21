# Data Ingestion
This repository creates an AWS Glue job using the logic in the `/src` directory

### Goal of Exercise
It is good practice to ingest data as-is (close to) as it can be expensive to ingest all of the data for every downstream transformation. It is also easier to debug.

Ingest input csv files and output them as parquet to specified locations:
- Make sure that Spark properly uses the csv header and separator
- Make sure that column names are compatible with Apache Parquet

## Quickstart
* Set up your [development environment](../development-environment.md)
* Run tests in the`data-ingestion` dir: `python -m pytest` (Fix the tests!)
* Deploy: simply push the code, Github Actions will deploy using the workflow for your branch
* [Run the AWS Glue job](https://docs.aws.amazon.com/glue/latest/dg/console-jobs.html)

## View the Spark UI
[Install the latest version of the SessionsManager CLI](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html).
From the root of the repository:
```
./data-derp bootstrap switch-role -p <project-name> -m <module-name>
./data-derp aws-spark-ui -p <project-name> -m <module-name>
```
Navigate to http://localhost:18080



