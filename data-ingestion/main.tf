locals {
  submodule-name    = "data-ingestion"
  source-bucket     = "${var.project-name}-${var.module-name}-data-source"
  target-bucket     = "${var.project-name}-${var.module-name}"
  spark-logs-bucket = "${var.project-name}-${var.module-name}-spark-logs"
}
module "glue-job" {
  source = "../terraform-modules/glue-job"

  project-name   = var.project-name
  module-name    = var.module-name
  submodule-name = local.submodule-name
  script-path    = "${local.submodule-name}/main.py"
  additional-params = {
    "--extra-py-files" : "s3://${local.target-bucket}/${local.submodule-name}/data_ingestion-0.1-py3.egg", # https://docs.aws.amazon.com/glue/latest/dg/reduced-start-times-spark-etl-jobs.html
    "--temperatures_country_input_path" : "s3://${local.source-bucket}/TemperaturesByCountry.csv",
    "--temperatures_country_output_path" : "s3://${local.target-bucket}/${local.submodule-name}/TemperaturesByCountry.parquet",
    "--temperatures_global_input_path" : "s3://${local.source-bucket}/GlobalTemperatures.csv",
    "--temperatures_global_output_path" : "s3://${local.target-bucket}/${local.submodule-name}/GlobalTemperatures.parquet",
    "--co2_input_path" : "s3://${local.source-bucket}/EmissionsByCountry.csv",
    "--co2_output_path" : "s3://${local.target-bucket}/${local.submodule-name}/EmissionsByCountry.parquet",
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
          "s3:ListBucket",
          "s3:GetObject"
        ],
        "Resource" : [
          "arn:aws:s3:::${local.source-bucket}",
          "arn:aws:s3:::${local.source-bucket}/*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "s3:ListBucket"
        ],
        "Resource" : [
          "arn:aws:s3:::${local.target-bucket}",
        ],
        "Condition" : {
          "StringLike" : {
            "s3:prefix" : "${local.submodule-name}*"
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
          "arn:aws:s3:::${local.target-bucket}/${local.submodule-name}",
          "arn:aws:s3:::${local.target-bucket}/${local.submodule-name}/*"
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