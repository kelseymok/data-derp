resource "aws_glue_catalog_database" "this" {
  name = "${var.project-name}-${var.module-name}-${var.submodule-name}"
}

resource "aws_glue_crawler" "this" {
  database_name = aws_glue_catalog_database.this.name
  name          = "${var.project-name}-${var.module-name}-${var.submodule-name}-crawler"
  role          = aws_iam_role.crawler.arn
  table_prefix  = "${var.project-name}_${var.module-name}_"

  s3_target {
    path       = "s3://${var.project-name}-${var.module-name}/${var.submodule-name}"
    exclusions = ["*.egg", "*.py", "athena/**", "Unsaved/**", "*.csv"]
  }
}

resource "aws_iam_role" "crawler" {
  name                  = "${var.project-name}-${var.module-name}-${var.submodule-name}-crawler"
  permissions_boundary  = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.project-name}-${var.module-name}/${var.project-name}-${var.module-name}-delegated-boundary"
  force_detach_policies = true
  assume_role_policy    = <<EOF
{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Action": "sts:AssumeRole",
        "Principal": {
          "Service": "glue.amazonaws.com"
        },
        "Effect": "Allow",
        "Sid": ""
      }
    ]
}
EOF
}

resource "aws_iam_policy" "crawler" {
  name = "${var.project-name}-${var.module-name}-${var.submodule-name}-crawler"
  policy = jsonencode({
    "Version" : "2012-10-17",
    "Statement" : [
      {
        "Effect" : "Allow",
        "Action" : [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        "Resource" : [
          "arn:aws:logs:*:*:/aws-glue/crawlers*"
        ]
      },
      {
        "Effect" : "Allow",
        "Action" : [
          "glue:GetDatabase",
          "glue:*Table*",
          "glue:*Partition*",
        ],
        "Resource" : [
          "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:catalog",
          "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:database/${aws_glue_catalog_database.this.name}",
          "arn:aws:glue:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:table/${aws_glue_catalog_database.this.name}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue-crawler-role" {
  role       = aws_iam_role.crawler.name
  policy_arn = aws_iam_policy.crawler.arn
}