locals {
  submodule-name    = "data-transformation"
  s3-bucket         = "${var.project-name}-${var.module-name}"
  s3-source-prefix  = "data-ingestion"
  spark-logs-bucket = "${var.project-name}-${var.module-name}-spark-logs"
}
module "glue-job" {
  source = "../terraform-modules/glue-job"

  project-name   = var.project-name
  module-name    = var.module-name
  submodule-name = local.submodule-name
  script-path    = "${local.submodule-name}/main.py"
  additional-params = {
    "--extra-py-files" : "s3://${local.s3-bucket}/${local.submodule-name}/data_transformation-0.1-py3.egg", # https://docs.aws.amazon.com/glue/latest/dg/reduced-start-times-spark-etl-jobs.html

    "--co2_input_path" : "s3://${local.s3-bucket}/${local.s3-source-prefix}/EmissionsByCountry.parquet/",
    "--temperatures_global_input_path" : "s3://${local.s3-bucket}/${local.s3-source-prefix}/GlobalTemperatures.parquet/",
    "--temperatures_country_input_path" : "s3://${local.s3-bucket}/${local.s3-source-prefix}/TemperaturesByCountry.parquet/",

    "--co2_temperatures_global_output_path" : "s3://${local.s3-bucket}/${local.submodule-name}/GlobalEmissionsVsTemperatures.parquet/",
    "--co2_temperatures_country_output_path" : "s3://${local.s3-bucket}/${local.submodule-name}/CountryEmissionsVsTemperatures.parquet/",
    "--europe_big_3_co2_output_path" : "s3://${local.s3-bucket}/${local.submodule-name}/EuropeBigThreeEmissions.parquet/",
    "--co2_oceania_output_path" : "s3://${local.s3-bucket}/${local.submodule-name}/OceaniaEmissionsEdited.parquet/",
  }
}

# access to S3
resource "aws_iam_role_policy_attachment" "s3-access" {
  role       = module.glue-job.job_role_name
  policy_arn = aws_iam_policy.s3-policy.arn
}

resource "aws_iam_policy" "s3-policy" {
  name = "${var.project-name}-${var.module-name}-${local.submodule-name}-s3"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:GetObject"
        ],
        "Resource" : [
          "arn:aws:s3:::${local.s3-bucket}/${local.s3-source-prefix}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:ListBucket"
        ],
        "Resource" : [
          "arn:aws:s3:::${local.s3-bucket}",
        ],
        "Condition" : {
          "StringLike" : {
            "s3:prefix" : ["${local.submodule-name}*", "${local.s3-source-prefix}*"]
          }
        }
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        "Resource" : [
          "arn:aws:s3:::${local.s3-bucket}/${local.submodule-name}",
          "arn:aws:s3:::${local.s3-bucket}/${local.submodule-name}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:*"
        ],
        "Resource" : [
          "arn:aws:s3:::${local.spark-logs-bucket}",
          "arn:aws:s3:::${local.spark-logs-bucket}/*"
        ]
      }
    ]
  })
}