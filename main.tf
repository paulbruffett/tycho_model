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