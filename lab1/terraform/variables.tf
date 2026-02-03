variable "instance_name" {
  description = "Value of the EC2 instance's Name."
  type        = string
  default     = "ubuntu"
}

variable "instance_type" {
  description = "The EC2 instance's type."
  type        = string
  default     = "t2.large"
}
