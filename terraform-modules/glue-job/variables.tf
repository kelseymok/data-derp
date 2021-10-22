variable "project-name" {
  type = string
}

variable "module-name" {
  type = string
}

variable "submodule-name" {
  type = string
}

variable "script-path" {
  description = "Script path in bucket (my-bucket/ingestion.py -> ingestion.py)"
  type        = string
}

variable "additional-params" {
  type    = map(string)
  default = {}
}