RGNAME=<Your RG>
AKSNAME=<Your AKS>
ACRNAME=<Your ACR>

# Create an AKS cluster with default settings
az aks create -g $RGNAME -n $AKSNAME --kubernetes-version 1.19.11

# Create an Azure Container Registry
az acr create --resource-group $RGNAME --name $ACRNAME --sku Basic

# Attach the ACR to the AKS cluster
az aks update -n $AKSNAME -g $RGNAME --attach-acr $ACRNAME



