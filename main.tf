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

     # Configure the Microsoft Azure Provider
     provider "azurerm" {
  features {}

    subscription_id = subscription_id
    client_id       = client_id
    client_secret   = client_secret
    tenant_id       = tenant_id
}

     # An example resource that does nothing.
    # Create a resource group
    resource "azurerm_resource_group" "example" {
    name     = "example-resources"
    location = "West Europe"
    }

    # Create a virtual network within the resource group
    resource "azurerm_virtual_network" "example" {
    name                = "example-network"
    resource_group_name = azurerm_resource_group.example.name
    location            = azurerm_resource_group.example.location
    address_space       = ["10.0.0.0/16"]
    }