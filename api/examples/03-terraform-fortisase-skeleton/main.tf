# Minimal FortiSASE config-plane example: manage an SPA service connection.
# Provider: fortinetdev/fortisase (first-party). Auth = FortiCloud IAM API user.
# Daniel: run `terraform init/plan` yourself — credentials are involved.
#
# This is the config plane only. Device onboarding (FortiGate/FortiAP) happens in
# FortiZTP/FortiManager first — see ../../reference/02-fortiztp-onramp.md.

terraform {
  required_version = ">= 1.0"
  required_providers {
    fortisase = {
      source  = "fortinetdev/fortisase"
      version = "~> 1.2"
    }
  }
}

variable "fsase_api_id"     { type = string, sensitive = true }
variable "fsase_api_secret" { type = string, sensitive = true }

provider "fortisase" {
  username = var.fsase_api_id     # supply via TF_VAR_fsase_api_id (never commit)
  password = var.fsase_api_secret
}

# --- SPA network configuration (the common BGP/overlay settings) ---------------
# NOTE: argument names below are illustrative — confirm against the provider docs
# (registry.terraform.io/providers/fortinetdev/fortisase) and the incoming Swagger
# before applying. SPA network config must exist before Branch On-ramp (corpus 01 §3.3).
#
# resource "fortisase_private_access_network_configuration" "spa" {
#   bgp_design          = "overlay"     # or "loopback"
#   hub_selection_method = "bgp-med"    # health-priority | bgp-med
# }

# --- SPA service connection to a FortiGate hub --------------------------------
# resource "fortisase_private_access_service_connections" "dc_hub" {
#   name        = "dc-hub-east"
#   # ...hub address, overlays, BGP neighbor params...
#   depends_on  = [fortisase_private_access_network_configuration.spa]
# }

# --- Read-only visibility into onboarded edges --------------------------------
data "fortisase_infra_fortigates" "edges" {}

output "onboarded_fortigates" {
  value = data.fortisase_infra_fortigates.edges
}
