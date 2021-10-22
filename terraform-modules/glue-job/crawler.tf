resource "aws_glue_catalog_database" "this" {
  name = "${var.project-name}-${var.module-name}-${var.submodule-name}"
}

resource "aws_glue_crawler" "this" {
  database_name = aws_glue_catalog_database.this.name
  name          = "${var.project-name}-${var.module-name}-${var.submodule-name}-crawler"
  role          = aws_iam_role.this.arn
  table_prefix  = "${var.project-name}_${var.module-name}_"

  s3_target {
    path       = "s3://${var.project-name}-${var.module-name}/${var.submodule-name}"
    exclusions = ["*.egg", "*.py", "athena/**", "Unsaved/**", "*.csv"]
  }
}