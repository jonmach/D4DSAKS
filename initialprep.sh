RGNAME=<Your RG>   # Your resource group
STG=<Your Storage> # Your storage account name
CON=<Your Storage Container>   # Your storage account container
EXPIRES=$(date --date='1 days' "+%Y-%m-%d")
IMAGEDIR="CIFAR-10-images"

az group create -l uksouth -n $RGNAME

az storage account create --name $STG --resource-group $RGNAME --location uksouth --sku Standard_ZRS  # Create Storage Account
az storage container create  --account-name $STG  --name $CON  --auth-mode login    # Create your storage container

ACCOUNTKEY=$(az storage account keys list --resource-group $RGNAME --account-name $STG | grep -i value | head -1 | cut -d':' -f2 | tr -d [\ \"])

# Generate a temporary SAS key
SAS=$(az storage container generate-sas --account-key $ACCOUNTKEY --account-name $STG --expiry $EXPIRES --name $CON --permissions acldrw | tr -d [\"]) 

# Determine your URL endpoint
STGURL=$(az storage account show --name $STG --query primaryEndpoints.blob | tr -d [\"])
CONURL="$STGURL$CON"

# Copy the files to your storage container
azcopy cp "$IMAGEDIR" "$CONURL?$SAS" --recursive

