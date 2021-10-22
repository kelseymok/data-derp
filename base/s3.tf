module "s3-bucket" {
  source = "../terraform-modules/s3-bucket"

  bucket-name   = "${var.project-name}-${var.module-name}"
  force-destroy = true
}