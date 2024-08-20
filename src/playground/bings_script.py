
## Placeholder for the Bings Ads Script
### Bing Script 

## Programatically getting the basic for this Bing Ads Call

## V0.1

### Required packages:
import requests
import csv
import hashlib
import shutil
import json
### IMPORTANT: The Base XML package of python is prone to vulnerabilities. I.E Billion Laughs Bomb. Using safer defusedxml package
from defusedxml.ElementTree import fromstring

### Functions Setup

## Why do we put the payload on one line: Payloads Fail with line break. 


## Step 1: Retrieval of User ID 

# Traverses the GetUserRequest SOAP XML tree response and retrieves the User ID
def getUserIdFromResponse(xmlRoot):
    ## TODO: Check if we can avoid this Nesting mess
    for branch in xmlRoot:
        if(branch.tag == "{http://schemas.xmlsoap.org/soap/envelope/}Body"): 
            for leaf in branch:
                if(leaf.tag == "{https://bingads.microsoft.com/Customer/v13}GetUserResponse"):
                    for subleaf in leaf:
                        if(subleaf.tag== "{https://bingads.microsoft.com/Customer/v13}User"):
                            for user_leaf in subleaf:
                                if(user_leaf.tag == "{https://bingads.microsoft.com/Customer/v13/Entities}Id"):
                                    return user_leaf.text 

# Container Function of the Get  User Process
def callGetUserRequestAndRetrieveUserId(developer_token, authentication_token):
    customer_manager_service_url = "https://clientcenter.api.sandbox.bingads.microsoft.com/Api/CustomerManagement/v13/CustomerManagementService.svc"
    payload = "<soapenv:Envelope xmlns:soapenv=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:v13=\"https://bingads.microsoft.com/Customer/v13\">\n   <soapenv:Header>\n      <v13:DeveloperToken>" + developer_token + "</v13:DeveloperToken>\n      <v13:AuthenticationToken>" + authentication_token + "</v13:AuthenticationToken>\n   </soapenv:Header>\n   <soapenv:Body>\n      <v13:GetUserRequest>\n         <v13:UserId xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:nil=\"true\"/>\n      </v13:GetUserRequest>\n   </soapenv:Body>\n</soapenv:Envelope>"
    headers = {
        'Content-Type': 'text/xml',
        'SOAPAction': 'GetUser'
    }

    response = requests.request("POST", customer_manager_service_url, headers=headers, data=payload)

    #print( "#####////######")
    #print(response.text)
    #print( "#####////######")

    return getUserIdFromResponse(fromstring(response.text))

## Step 2 : Retrieve the Account
## TODO: What happens if the base account has multiple accounts?

def getAccountIdFromResponse(xmlRoot):
    ## TODO: Check if we can avoid this Nesting mess
    for branch in xmlRoot:
        if(branch.tag == "{http://schemas.xmlsoap.org/soap/envelope/}Body"): 
            for leaf in branch:
                if(leaf.tag == "{https://bingads.microsoft.com/Customer/v13}SearchAccountsResponse"):
                    for subleaf in leaf:
                        ## TODO: Expand for Multiple accounts
                        if(subleaf.tag== "{https://bingads.microsoft.com/Customer/v13}Accounts"):
                            for account_leaf in subleaf:
                                if(account_leaf.tag == "{https://bingads.microsoft.com/Customer/v13/Entities}AdvertiserAccount"):
                                    for ads_account_leaf in account_leaf:
                                        if(ads_account_leaf.tag == "{https://bingads.microsoft.com/Customer/v13/Entities}Id"):
                                            return ads_account_leaf.text 

def callGetAccountRequestAndRetrieveAccountId(developer_token, authentication_token, user_id):
    customer_manager_service_url = "https://clientcenter.api.sandbox.bingads.microsoft.com/Api/CustomerManagement/v13/CustomerManagementService.svc"
    payload = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\">\n  <s:Header>\n    <h:ApplicationToken i:nil=\"true\" xmlns:h=\"https://bingads.microsoft.com/Customer/v13\" xmlns:i=\"http://www.w3.org/2001/XMLSchema-instance\" />\n    <h:AuthenticationToken xmlns:h=\"https://bingads.microsoft.com/Customer/v13\">"+ authentication_token + "</h:AuthenticationToken>\n    <h:DeveloperToken xmlns:h=\"https://bingads.microsoft.com/Customer/v13\">" + developer_token + "</h:DeveloperToken>\n  </s:Header>\n  <s:Body>\n    <SearchAccountsRequest xmlns=\"https://bingads.microsoft.com/Customer/v13\">\n      <Predicates xmlns:a=\"https://bingads.microsoft.com/Customer/v13/Entities\" xmlns:i=\"http://www.w3.org/2001/XMLSchema-instance\">\n        <a:Predicate>\n          <a:Field>UserId</a:Field>\n          <a:Operator>Equals</a:Operator>\n          <a:Value>"+ user_id +"</a:Value>\n        </a:Predicate>\n      </Predicates>\n      <Ordering i:nil=\"true\" xmlns:a=\"https://bingads.microsoft.com/Customer/v13/Entities\" xmlns:i=\"http://www.w3.org/2001/XMLSchema-instance\" />\n      <PageInfo xmlns:a=\"https://bingads.microsoft.com/Customer/v13/Entities\" xmlns:i=\"http://www.w3.org/2001/XMLSchema-instance\">\n        <a:Index>0</a:Index>\n        <a:Size>10</a:Size>\n      </PageInfo>\n    </SearchAccountsRequest>\n  </s:Body>\n</s:Envelope>\n"

    headers = {
    'Content-Type': 'text/xml',
    'SOAPAction': 'SearchAccounts'
    }

    response = requests.request("POST", customer_manager_service_url, headers=headers, data=payload)

    #print(response.text)

    return getAccountIdFromResponse(fromstring(response.text))

### Step 3

def getAudiencesIDFromLeaf(xmlLeaf):
    ## TODO: Check if we can avoid this Nesting mess
    audience_ids = []
    for subleaf in xmlLeaf:
        ## TODO: Expand for Multiple accounts
        if(subleaf.tag == "{https://bingads.microsoft.com/CampaignManagement/v13}Audiences"):
            for audience_leaf in subleaf:
                if(audience_leaf.tag == "{https://bingads.microsoft.com/CampaignManagement/v13}Audience"):
                    for audience_entity in audience_leaf:
                        if(audience_entity.tag == "{https://bingads.microsoft.com/CampaignManagement/v13}Id"):
                            audience_ids.append(audience_entity.text)
                            break
    
    return audience_ids


def getAudiencesIDsfromResponse(xmlRoot):
    ## TODO: Check if we can avoid this Nesting mess
    for branch in xmlRoot:
        if(branch.tag == "{http://schemas.xmlsoap.org/soap/envelope/}Body"): 
            for leaf in branch:
                if(leaf.tag == "{https://bingads.microsoft.com/CampaignManagement/v13}GetAudiencesByIdsResponse"):
                    return getAudiencesIDFromLeaf(leaf) 
                                        

def callGetCustomerListAudiencesByAccounts(developer_token, authentication_token, user_id, account_id):
    campaing_manager_service_url = "https://campaign.api.sandbox.bingads.microsoft.com/Api/Advertiser/CampaignManagement/v13/CampaignManagementService.svc"
    payload = "<s:Envelope xmlns:i=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\">\n  <s:Header xmlns=\"https://bingads.microsoft.com/CampaignManagement/v13\">\n    <Action mustUnderstand=\"1\">GetAudiencesByIds</Action>\n   <AuthenticationToken i:nil=\"false\">" + authentication_token + "</AuthenticationToken>\n  <CustomerAccountId i:nil=\"false\">" + account_id + "</CustomerAccountId>\n    <CustomerId i:nil=\"false\">" + user_id + "</CustomerId>\n    <DeveloperToken i:nil=\"false\">" + developer_token + "</DeveloperToken>\n  </s:Header>\n  <s:Body>\n    <GetAudiencesByIdsRequest xmlns=\"https://bingads.microsoft.com/CampaignManagement/v13\">\n      <Type>CustomerList</Type>\n    </GetAudiencesByIdsRequest>\n  </s:Body>\n</s:Envelope>\n"
    headers = {
    'Content-Type': 'text/xml',
    'SOAPAction': 'GetAudiencesByIds',
    }

    response = requests.request("POST", campaing_manager_service_url, headers=headers, data=payload)
    return getAudiencesIDsfromResponse(fromstring(response.text))

### Step 4 > Build the CSV
def createCSVForRemovingCustomerListObject(audiences_ids,target_email):
    base_filepath = "fixtures/CustomerListRemoval.csv"
    destination  = "CustomerListRemoval.csv"
    csv_headers = ["Type","Status","Id","Parent Id","Client Id","Modified Time","Name","Description","Scope","Audience","Action Type","SubType","Text"]
    print("Target Email to remove:" + target_email)
    ## Hash the Email
    hashedEmail=hashlib.sha256(target_email.encode()).hexdigest()
    print(" Hashed Email>> " + hashedEmail)
    ## Copy the Fixture File
    shutil.copyfile(base_filepath, destination)

    with open(destination,'a') as csvfile:
        writer = csv.DictWriter(csvfile,csv_headers)
        for audience_id in audiences_ids:
            writer.writerow({"Type": "Customer List", "Id": audience_id, "Client Id": "fides_ethyca", "Action Type": "Update" })
            writer.writerow({"Type": "Customer List Item", "Parent Id": audience_id, "Action Type": "Delete", "SubType": "Email", "Text": hashedEmail})

### Step 5 > Get the Bulk Upload URL

def getUploadURLFromResponse(xmlRoot):
    for branch in xmlRoot:
        if(branch.tag == "{http://schemas.xmlsoap.org/soap/envelope/}Body"): 
            for leaf in branch:
                if(leaf.tag == "{https://bingads.microsoft.com/CampaignManagement/v13}GetBulkUploadUrlResponse"):
                    for subleaf in leaf:
                        if(subleaf.tag== "{https://bingads.microsoft.com/CampaignManagement/v13}UploadUrl"):
                             return subleaf.text 

def getBulkUploadURL(developer_token, authentication_token, user_id, account_id):
    bulk_api_url = "https://bulk.api.sandbox.bingads.microsoft.com/Api/Advertiser/CampaignManagement/v13/BulkService.svc?wsdl"

    payload = "<s:Envelope xmlns:i=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\">\n  <s:Header xmlns=\"https://bingads.microsoft.com/CampaignManagement/v13\">\n    <Action mustUnderstand=\"1\">GetBulkUploadUrl</Action>\n   <AuthenticationToken i:nil=\"false\">" + authentication_token +   "</AuthenticationToken>\n    <CustomerAccountId i:nil=\"false\">" + account_id + "</CustomerAccountId>\n    <CustomerId i:nil=\"false\">" + user_id +"</CustomerId>\n    <DeveloperToken i:nil=\"false\">"+  developer_token + "</DeveloperToken>\n  </s:Header>\n  <s:Body>\n    <GetBulkUploadUrlRequest xmlns=\"https://bingads.microsoft.com/CampaignManagement/v13\">\n      <ResponseMode>ErrorsAndResults</ResponseMode>\n      <AccountId>" + account_id + "</AccountId>\n    </GetBulkUploadUrlRequest>\n  </s:Body>\n</s:Envelope>\n"
    headers = {
        'Content-Type': 'text/xml',
        'SOAPAction': 'GetBulkUploadUrl',
    }

    response = requests.request("POST", bulk_api_url, headers=headers, data=payload)

    return getUploadURLFromResponse(fromstring(response.text))

### Step 6 : Upload to the API 

def bulkUploadCustomerList(url,developer_token, authentication_token, user_id, account_id ):

    url = "https://fileupload.api.sandbox.bingads.microsoft.com/Api/Advertiser/CampaignManagement/FileUpload/File/UploadBulkFile/4bba40a0-3f2c-4242-ab08-3c166e833586?Ver=13"

    payload = {'AuthenticationToken': authentication_token,
    'DeveloperToken': developer_token,
    'CustomerId': user_id,
    'AccountId': account_id}
    files=[
        ('uploadFile',('customerlist.csv',open('CustomerListRemoval.csv','rb'),'application/octet-stream'))
    ]

    headers = {
    'Authorization': 'Bearer' + authentication_token
    }

    response = requests.request("POST", url, headers=headers, data=payload, files=files)

    return json.loads(response.text)


### Variables Setup
## On the Bings Sandbox enviroment, we dont need to specify the Dev token, since its always the same Token
## Outside Sanbox, we would need to set up the Flow to get the developer token
# Oh what that means we need to do it, dosent it? /s

sandbox_developer_token = "BBD37VB98"
current_authentication_token = "eyJhbGciOiJSU0EtT0FFUCIsImVuYyI6IkExMjhDQkMtSFMyNTYiLCJ4NXQiOiJJekQ3cTdrcUowdzU0R0wxVUJtT3FHMU9JS0kiLCJ6aXAiOiJERUYifQ.KMko1d7qFCrt65CypzFmuCqt25oHhEhmiie1lZV_FxeP8HzbOjBIW4oJHxwRSQ79SIGn-Ngi6z-32uraZW_cNgBv0UrGWqxOEbhTl6qluDOjP3qiKGu0qGz3tOspjsr6EGXf0118qHXx3Tvo2KrwCPNayUMU7PKsBsm9XuLd2NoTc5-f2gRd-o6-p1-4Zo91mwpRA-FemZpgjFHhH5EYmwgOTwAC9nqLLqtIuuzqjXIkdDLSwxbkw9tINDtrgBjLcijDl3shfWGkpYYgeilP0b56lQUMQq07P7AVzXk8r7KGr_KNUDsRM24MBgCbGJeLRQzCHdu0A2BcpqwwEwkI6A.SfQdsBdwtOC3aBQbh-dLPQ.iTaeopzgt17VAbAKf6H2eyIguyFmqVB3iH2rFTNn-yHHBCh3VJOa4X7NK9bz4NMEZvDZvCoJZz7BquD3H6UPDesk-g_mNF3sS94S1pKg9TgVYQytRJBpjNC-8UmFEpKORK67et2i-GTUYHNzlOsrp5E26WArbeT7RJmxOW7iYh9hrp1Fkk7_87ofi3gHoHmrsaKBQqMnJFnNWHvAzaSz2nExfyl1t5zvg4MxgysgvPsdO5QQIcwlYCTSLfEztqG57cZ1TDOE-QbwwIh8ocCb435ENvi9qXvULcN10K-FMtTXKu96wvPV_fLx2q0B_ohixRIQtronXRfr1ZYGMhsZ02gNnl3IZuDcAobUAv_QfxJJgC7Je311ouMv9zC23-hI7poPYHUgHxWvziaz_vmRqMu2X90bEGU7XL5QECUM8W1uPl1jYzlGYZsjMj2gxkJ8UvIx3euOW3l1_ZTV5xShh9UxBrx66mwYvApO8WmGc8IYeCg7KmgUvVZmIF03rW5feK8PCzt84HsAMqU9shCcLWmhrByoB53ew7LuzjPIEB5GG-ZphqLdDSMp4Wr_u0_-mjZWxVK0Vtk2kCK6WgXjT0fgpkAxj5kH4SvtzF5L6l3Gu9B-VtF2ywoy9Ec4065p-Fi3vAoaAs6RPWMlp0Oc05PErawv1P1myotAb9QocRbhHQwD2LmX5_1vlIQ2lfxh6TXYk64NMqr3bYsMiG2M7PXC9JpgH-FbgM7LVgUDKYxArBPg3gi5vGbbSL7gyVbhAJgDwZzyYHLkUzhavS2NpUTyxdrm0cPzvXa9R130Q3AjXplbm4DZv03Y9r9sO8IM0HYMZBzkL4RTKV98DUIIe89_SOdjA8pZk1DG86KleOjyk9-CXJTWiZZP8wurNrtZ3Z4bryaagQbg-AkI4AjsrGrwcTFpWIdLXm4p98t0ByYcUdnrH3z31O45CWeQXacQOQk1tD6ixqWS1Hikkv8CoAfxwQvRSWNiM2UmNnxp28i2t30cEg2e2wN9V3xSDaftwcE1dyrKKryr4Ql37Wbv7GfSE44MAFyoNaJpjUx59L98dbPGfTLOM81gwC2arW8DYsSHmsctYTea-EwSKpwGRbbQyLf1LDd0YgADAk63X9GMyIBhehQp9Z99jglt1HStmiAsNpQno276_ndCdJzEtlnErYNCZ1JaUjffzPn7R1rztltadjlOCppC0VdqwxyAHNiH0EL0JSeQcKzbfUUzeC_5iYUJrAMcDsSwB9cqh2QX2v4gljKeN1gWUGGzWWQ3rxj2SH8abJHFdqB1tT9OxFSeqFbTDZxp_qces0Xs-2Vnj2xfRofab88hyVQ_tgN-XsXY9PservIoDA1_RhLytiMdmy6e0HevBWr421X_PktzHTZW5IR3XiZOBcNLEa9kEGkZTkx8bWnrVJlyLTqUemo6yPZzJ5hdCvDZvoJrcz807mibp3MywjVke2xyt0xDVnV7hw7WAEor4uEekE_6PA.YLzROApiy8XWW9BKmGwLYg"

print("Call numero One ######")
user_id = callGetUserRequestAndRetrieveUserId(sandbox_developer_token, current_authentication_token)
print("Gathered User Id:",user_id)

print("Call Numbe Dos ######")
account_id = callGetAccountRequestAndRetrieveAccountId(sandbox_developer_token, current_authentication_token, user_id)
print("Gathered Account Id:",account_id)
                              
print ("Llamada Number 3")
audience_ids = callGetCustomerListAudiencesByAccounts(sandbox_developer_token,current_authentication_token, user_id, account_id)
print("Gathered Audience IDs:")
print(audience_ids)

print("Building the  CSV")
createCSVForRemovingCustomerListObject(audience_ids,"someemail@data.cl")

print("Llamada 4, Obteniendo el Bulk Upload URL")

upload_url = getBulkUploadURL(sandbox_developer_token,current_authentication_token,user_id,account_id)

print("Upload URL: "+ upload_url)

print("Llamada 5: Uploading Customer List File")
response = bulkUploadCustomerList(upload_url,sandbox_developer_token,current_authentication_token,user_id,account_id)
print(response["TrackingId"])



