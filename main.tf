terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "=2.64.0"
    }
  }
  backend "remote" {
    # The name of your Terraform Cloud organization.
    organization = "pbazure"

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
  location = "West US"
}

resource "azurerm_application_insights" "aml" {
  name                = "tycho-model-ai"
  location            = azurerm_resource_group.aml.location
  resource_group_name = azurerm_resource_group.aml.name
  application_type    = "web"
}

resource "azurerm_key_vault" "aml" {
  name                     = "tychoworkeyvault7ee732bc"
  location                 = azurerm_resource_group.aml.location
  resource_group_name      = azurerm_resource_group.aml.name
  tenant_id                = data.azurerm_client_config.current.tenant_id
  sku_name                 = "standard"
  purge_protection_enabled = true
}

#storage information
resource "azurerm_storage_account" "aml" {
  name                     = "tychomodelstorage"
  location                 = azurerm_resource_group.aml.location
  resource_group_name      = azurerm_resource_group.aml.name
  account_tier             = "Standard"
  account_replication_type = "GRS"
}
resource "azurerm_storage_container" "aml" {
  name                  = "tycho-words"
  storage_account_name  = azurerm_storage_account.aml.name
  container_access_type = "private"
}

resource "azurerm_container_registry" "aml" {
  name                = "tychomlregistry"
  location            = azurerm_resource_group.aml.location
  resource_group_name = azurerm_resource_group.aml.name
  sku                 = "Basic"
}


resource "azurerm_machine_learning_workspace" "aml" {
  name                    = "tycho-workspace"
  location                = azurerm_resource_group.aml.location
  resource_group_name     = azurerm_resource_group.aml.name
  application_insights_id = azurerm_application_insights.aml.id
  key_vault_id            = azurerm_key_vault.aml.id
  storage_account_id      = azurerm_storage_account.aml.id
  container_registry_id   = azurerm_container_registry.aml.id

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_virtual_network" "aml" {
  name                = "aml-vnet"
  address_space       = ["10.1.0.0/16"]
  location            = azurerm_resource_group.aml.location
  resource_group_name = azurerm_resource_group.aml.name
}

resource "azurerm_subnet" "aml" {
  name                 = "aml-subnet"
  resource_group_name  = azurerm_resource_group.aml.name
  virtual_network_name = azurerm_virtual_network.aml.name
  address_prefixes     = ["10.1.0.0/24"]
}

resource "azurerm_machine_learning_compute_cluster" "aml" {
  name                          = "pbgpu"
  location                      = azurerm_resource_group.aml.location
  vm_priority                   = "Dedicated"
  vm_size                       = "Standard_NV12s_v3"
  machine_learning_workspace_id = azurerm_machine_learning_workspace.aml.id
  subnet_resource_id            = azurerm_subnet.aml.id

  scale_settings {
    min_node_count                   = 0
    max_node_count                   = 1
    scale_down_nodes_after_idle_duration = "PT30S" # 30 seconds
  }

  identity {
    type = "SystemAssigned"
  }
}