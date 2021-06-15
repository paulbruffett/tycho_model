terraform {
       backend "remote" {
         # The name of your Terraform Cloud organization.
         organization = "example-organization"

         # The name of the Terraform Cloud workspace to store Terraform state files in.
         workspaces {
           name = "tycho_model"
         }
       }
     }

     variable "subscription_id" {
         type = string
     }
     variable "client_id" {
         type = string
     }
     variable "client_secret" {
         type = string
     }
     variable "tenant_id" {
         type = string
     }

     # Configure the Microsoft Azure Provider
     provider "azurerm" {
  features {}

    subscription_id = var.subscription_id
    client_id       = var.client_id
    client_secret   = var.client_secret
    tenant_id       = var.tenant_id
}


data "azurerm_client_config" "current" {}

resource "azurerm_resource_group" "aml" {
  name     = "azure-ml"
  location = "West US 2"
}

resource "azurerm_application_insights" "aml" {
  name                = "workspace-example-ai"
  location            = azurerm_resource_group.aml.location
  resource_group_name = azurerm_resource_group.aml.name
  application_type    = "web"
}

resource "azurerm_key_vault" "aml" {
  name                = "workspaceexamplekeyvault"
  location            = azurerm_resource_group.aml.location
  resource_group_name = azurerm_resource_group.aml.name
  tenant_id           = data.azurerm_client_config.current.tenant_id
  sku_name            = "standard"
}

resource "azurerm_storage_account" "aml" {
  name                     = "workspacestorageaccount"
  location                 = azurerm_resource_group.aml.location
  resource_group_name      = azurerm_resource_group.aml.name
  account_tier             = "Standard"
  account_replication_type = "GRS"
}

resource "azurerm_machine_learning_workspace" "aml" {
  name                    = "tycho-workspace"
  location                = azurerm_resource_group.aml.location
  resource_group_name     = azurerm_resource_group.aml.name
  application_insights_id = azurerm_application_insights.aml.id
  key_vault_id            = azurerm_key_vault.aml.id
  storage_account_id      = azurerm_storage_account.aml.id

  identity {
    type = "SystemAssigned"
  }
}