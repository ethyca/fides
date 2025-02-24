# iabgpp-es

Encode/decode consent information with the IAB GPP Framework

(https://iabtechlab.com/gpp/)

## Methods available to CMPs

```javascript
constructor(cmpId: number, cmpVersion: number, customCommands?: CustomCommands)
fireEvent(eventName: string, value: any)
fireErrorEvent(value: string)
fireSectionChange(value: string)
getEventStatus()
setEventStatus(eventStatus: EventStatus)
getCmpStatus()
setCmpStatus(cmpStatus: CmpStatus)
getCmpDisplayStatus(): CmpDisplayStatus
setCmpDisplayStatus(cmpDisplayStatus: CmpDisplayStatus)
getApplicableSections(): number[]
setApplicableSections(applicableSections: number[]): void
getSignalStatus(): SignalStatus
setSignalStatus(signalStatus: SignalStatus): void
setGppString(encodedGppString: string): void
getGppString(): string
setSectionString(sectionName: string, encodedSectionString: string): void
setSectionStringById(sectionId: number, encodedSectionString: string): void
getSectionString(sectionName: string): string
getSectionStringById(sectionId: number): string
setFieldValue(sectionName: string, fieldName: string, value: any): void
setFieldValueBySectionId(sectionId: number, fieldName: string, value: any)
getFieldValue(sectionName: string, fieldName: string): any
getFieldValueBySectionId(sectionId: number, fieldName: string)
getSection(sectionName: string): any
getSectionById(sectionId: number): any
hasSection(sectionName: string): any
hasSectionId(sectionId: number): any
deleteSection(sectionName: string)
deleteSectionById(sectionId: number)
clear()
getObject()
getGvlFromVendorList(vendorList: VendorList): GVL
async getGvlFromUrl(gvlUrlConfig: GVLUrlConfig): Promise<GVL>
```

## Commands available to consumers

```javascript
__gpp("addEventListener", callback?, parameter?)
__gpp("getField", callback?, parameter?)
__gpp("getSection", callback?, parameter?)
__gpp("hasSection", callback?, parameter?)
__gpp("ping", callback?, parameter?)
__gpp("removeEventListener", callback?, parameter?)
```

## CMP usage Example

```javascript
<script>
  import {CmpApi} from '@iabgpp/cmpapi'; const cmpApi = new CmpApi(1, 3); cmpApi.setGppString(gppString);
  cmpApi.setFieldValue("uspv1", "OptOutSale", 0); cmpApi.fireUpdate("uspv1"); console.log(cmpApi.getGppString());
</script>
```

## Consumer usage example

```javascript
<script src="/js/stub/stub.js"></script>
<script>
  console.log(__gpp("ping"));

  __gpp("addEventListener", function (evt) {
    console.log("Received uspv1 event: " + evt);
    console.log(__gpp("getGPPString"));
  }, "uspv1");

  if(__gpp("hasSection", null, "tcfeuv2")) {
    console.log(__gpp("getSection", null, "tcfeuv2"));
  }

  if(__gpp("hasSection", null, "uspv1")) {
    console.log(__gpp("getField", null, "uspv1.OptOutSale"));
  }
</script>
```

## Fields

| Section Name | Section ID | Field                               | Data Type/Value                                                |
| ------------ | ---------- | ----------------------------------- | -------------------------------------------------------------- |
| tcfeuv2      | 2          | Version                             | 6 bit int. Value is 2.                                         |
| tcfeuv2      | 2          | Created                             | Datetime. Updated when fields are set                          |
| tcfeuv2      | 2          | LastUpdated                         | Datetime. Updated when fields are set                          |
| tcfeuv2      | 2          | CmpId                               | 12 bit int                                                     |
| tcfeuv2      | 2          | CmpVersion                          | 12 bit int                                                     |
| tcfeuv2      | 2          | ConsentScreen                       | 6 bit int                                                      |
| tcfeuv2      | 2          | ConsentLanguage                     | 2 character country code                                       |
| tcfeuv2      | 2          | VendorListVersion                   | 12 bit int                                                     |
| tcfeuv2      | 2          | PolicyVersion                       | 6 bit int. Value is 2                                          |
| tcfeuv2      | 2          | IsServiceSpecific                   | Boolean                                                        |
| tcfeuv2      | 2          | UseNonStandardStacks                | Boolean                                                        |
| tcfeuv2      | 2          | SpecialFeatureOptins                | Boolean array of size 12                                       |
| tcfeuv2      | 2          | PurposeConsents                     | Boolean array of size 24                                       |
| tcfeuv2      | 2          | PurposeLegitimateInterests          | Boolean array of size 24                                       |
| tcfeuv2      | 2          | PurposeOneTreatment                 | Boolean                                                        |
| tcfeuv2      | 2          | PublisherCountryCode                | 2 character country code                                       |
| tcfeuv2      | 2          | VendorConsents                      | Integer array of variable size                                 |
| tcfeuv2      | 2          | VendorLegitimateInterests           | Integer array of variable size                                 |
| tcfeuv2      | 2          | PublisherRestrictions               | Integer array of variable size                                 |
| tcfeuv2      | 2          | PublisherPurposesSegmentType        | 3 bit int. Value is 3                                          |
| tcfeuv2      | 2          | PublisherConsents                   | Boolean array of size 24                                       |
| tcfeuv2      | 2          | PublisherLegitimateInterests        | Boolean array of size 24                                       |
| tcfeuv2      | 2          | NumCustomPurposes                   | 6 bit int                                                      |
| tcfeuv2      | 2          | PublisherCustomConsents             | Boolean array where size is set by the NumCustomPurposes field |
| tcfeuv2      | 2          | PublisherCustomLegitimateInterests  | Boolean array where size is set by the NumCustomPurposes field |
| tcfeuv2      | 2          | VendorsAllowedSegmentType           | 3 bit int. Value is 2                                          |
| tcfeuv2      | 2          | VendorsAllowed                      | Integer array of variable size                                 |
| tcfeuv2      | 2          | VendorsDisclosedSegmentType         | 3 bit int. Value is 1                                          |
| tcfeuv2      | 2          | VendorsDisclosed                    | Integer array of variable size                                 |
| tcfcav1      | 5          | Version                             | 6 bit int. Value is 2.                                         |
| tcfcav1      | 5          | Created                             | Datetime. Updated when any fields are set                      |
| tcfcav1      | 5          | LastUpdated                         | Datetime. Updated when any fields are set                      |
| tcfcav1      | 5          | CmpId                               | 12 bit int                                                     |
| tcfcav1      | 5          | CmpVersion                          | 12 bit int                                                     |
| tcfcav1      | 5          | ConsentScreen                       | 6 bit int                                                      |
| tcfcav1      | 5          | ConsentLanguage                     | 2 character country code                                       |
| tcfcav1      | 5          | VendorListVersion                   | 12 bit int                                                     |
| tcfcav1      | 5          | TcfPolicyVersion                    | 6 bit int. Value is 2.                                         |
| tcfcav1      | 5          | UseNonStandardStacks                | Boolean                                                        |
| tcfcav1      | 5          | SpecialFeatureExpressConsent        | Boolean array of size 12                                       |
| tcfcav1      | 5          | PurposesExpressConsent              | Boolean array of size 24                                       |
| tcfcav1      | 5          | PurposesImpliedConsent              | Boolean array of size 24                                       |
| tcfcav1      | 5          | VendorExpressConsent                | Integer array of variable size                                 |
| tcfcav1      | 5          | VendorImpliedConsent                | Integer array of variable size                                 |
| tcfcav1      | 5          | PubRestrictions                     | RangeEntry list of variable size                               |
| tcfcav1      | 5          | PubPurposesSegmentType              | 3 bit int. Value is 3                                          |
| tcfcav1      | 5          | PubPurposesExpressConsent           | Boolean array of size 24                                       |
| tcfcav1      | 5          | PubPurposesImpliedConsent           | Boolean array of size 24                                       |
| tcfcav1      | 5          | NumCustomPurposes                   | 6 bit int                                                      |
| tcfcav1      | 5          | CustomPurposesExpressConsent        | Boolean array where size is set by the NumCustomPurposes field |
| tcfcav1      | 5          | CustomPurposesImpliedConsent        | Boolean array where size is set by the NumCustomPurposes field |
| tcfcav1      | 5          | DisclosedVendorsSegmentType         | 3 bit int. Value is 1                                          |
| tcfcav1      | 5          | DisclosedVendors                    | Integer list of variable size                                  |
| uspv1        | 6          | Version                             | 6 bit int. Value is 1                                          |
| uspv1        | 6          | Notice                              | 2 bit int                                                      |
| uspv1        | 6          | OptOutSale                          | 2 bit int                                                      |
| uspv1        | 6          | LspaCovered                         | 2 bit int                                                      |
| usnat        | 7          | Version                             | 6 bit int. Value is 1                                          |
| usnat        | 7          | SharingNotice                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SharingOptOutNotice                 | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SensitiveDataProcessingOptOutNotice | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SensitiveDataLimitUseNotice         | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SharingOptOut                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | SensitiveDataProcessing             | 2 bit int array of size 16. 0=Not applicable, 1=Yes, 2=No      |
| usnat        | 7          | KnownChildSensitiveDataConsents     | 2 bit int array of size 3. 0=Not applicable, 1=Yes, 2=No       |
| usnat        | 7          | PersonalDataConsents                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnat        | 7          | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usnat        | 7          | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usnat        | 7          | Gpc                                 | Boolean                                                        |
| usca         | 8          | Version                             | 6 bit int. Value is 1                                          |
| usca         | 8          | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | SharingOptOutNotice                 | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | SensitiveDataLimitUseNotice         | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | SharingOptOut                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | SensitiveDataProcessing             | 2 bit int array of size 9. 0=Not applicable, 1=Yes, 2=No       |
| usca         | 8          | KnownChildSensitiveDataConsents     | 2 bit int array of size 2. 0=Not applicable, 1=Yes, 2=No       |
| usca         | 8          | PersonalDataConsents                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usca         | 8          | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usca         | 8          | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usca         | 8          | Gpc                                 | Boolean                                                        |
| usva         | 9          | Version                             | 6 bit int. Value is 1                                          |
| usva         | 9          | SharingNotice                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usva         | 9          | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usva         | 9          | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | Version                             | 6 bit int. Value is 1                                          |
| usco         | 10         | SharingNotice                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | SensitiveDataProcessing             | 2 bit int array of size 7. 0=Not applicable, 1=Yes, 2=No       |
| usco         | 10         | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usco         | 10         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usco         | 10         | GpcSegmentIncluded                  | Boolean. Deafult is true                                       |
| usco         | 10         | Gpc                                 | Boolean                                                        |
| usut         | 11         | Version                             | 6 bit int. Value is 1                                          |
| usut         | 11         | SharingNotice                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | SensitiveDataProcessingOptOutNotice | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usut         | 11         | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usut         | 11         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | Version                             | 6 bit int. Value is 1                                          |
| usct         | 12         | SharingNotice                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usct         | 12         | KnownChildSensitiveDataConsents     | 2 bit int array of size 3. 0=Not applicable, 1=Yes, 2=No       |
| usct         | 12         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usct         | 12         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usct         | 12         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usct         | 12         | Gpc                                 | Boolean                                                        |
| usfl         | 13         | Version                             | 6 bit int. Value is 1                                          |
| usfl         | 13         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usfl         | 13         | KnownChildSensitiveDataConsents     | 2 bit int array of size 3. 0=Not applicable, 1=Yes, 2=No       |
| usfl         | 13         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usfl         | 13         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | Version                             | 6 bit int. Value is 1                                          |
| usmt         | 14         | SharingNotice                       | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usmt         | 14         | KnownChildSensitiveDataConsents     | 2 bit int array of size 3. 0=Not applicable, 1=Yes, 2=No       |
| usmt         | 14         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usmt         | 14         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usmt         | 14         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usmt         | 14         | Gpc                                 | Boolean                                                        |
| usor         | 15         | Version                             | 6 bit int. Value is 1                                          |
| usor         | 15         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | SensitiveDataProcessing             | 2 bit int array of size 11. 0=Not applicable, 1=Yes, 2=No      |
| usor         | 15         | KnownChildSensitiveDataConsents     | 2 bit int array of size 3. 0=Not applicable, 1=Yes, 2=No       |
| usor         | 15         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usor         | 15         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usor         | 15         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usor         | 15         | Gpc                                 | Boolean                                                        |
| ustx         | 16         | Version                             | 6 bit int. Value is 1                                          |
| ustx         | 16         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| ustx         | 16         | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustx         | 16         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| ustx         | 16         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| ustx         | 16         | Gpc                                 | Boolean                                                        |
| usde         | 17         | Version                             | 6 bit int. Value is 1                                          |
| usde         | 17         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | SensitiveDataProcessing             | 2 bit int array of size 9. 0=Not applicable, 1=Yes, 2=No       |
| usde         | 17         | KnownChildSensitiveDataConsents     | 2 bit int array of size 5. 0=Not applicable, 1=Yes, 2=No       |
| usde         | 17         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usde         | 17         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usde         | 17         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usde         | 17         | Gpc                                 | Boolean                                                        |
| usia         | 18         | Version                             | 6 bit int. Value is 1                                          |
| usia         | 18         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | SensitiveDataOptOutNotice           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usia         | 18         | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usia         | 18         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usia         | 18         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usia         | 18         | Gpc                                 | Boolean                                                        |
| usne         | 19         | Version                             | 6 bit int. Value is 1                                          |
| usne         | 19         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usne         | 19         | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usne         | 19         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usne         | 19         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usne         | 19         | Gpc                                 | Boolean                                                        |
| usnh         | 20         | Version                             | 6 bit int. Value is 1                                          |
| usnh         | 20         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| usnh         | 20         | KnownChildSensitiveDataConsents     | 2 bit int array of size 3. 0=Not applicable, 1=Yes, 2=No       |
| usnh         | 20         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnh         | 20         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usnh         | 20         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usnh         | 20         | Gpc                                 | Boolean                                                        |
| usnj         | 21         | Version                             | 6 bit int. Value is 1                                          |
| usnj         | 21         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | SensitiveDataProcessing             | 2 bit int array of size 10. 0=Not applicable, 1=Yes, 2=No      |
| usnj         | 21         | KnownChildSensitiveDataConsents     | 2 bit int array of size 5. 0=Not applicable, 1=Yes, 2=No       |
| usnj         | 21         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| usnj         | 21         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| usnj         | 21         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| usnj         | 21         | Gpc                                 | Boolean                                                        |
| ustn         | 22         | Version                             | 6 bit int. Value is 1                                          |
| ustn         | 22         | ProcessingNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | SaleOptOutNotice                    | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | TargetedAdvertisingOptOutNotice     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | SaleOptOut                          | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | TargetedAdvertisingOptOut           | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | SensitiveDataProcessing             | 2 bit int array of size 8. 0=Not applicable, 1=Yes, 2=No       |
| ustn         | 22         | KnownChildSensitiveDataConsents     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | AdditionalDataProcessingConsent     | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | MspaCoveredTransaction              | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | MspaOptOutOptionMode                | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | MspaServiceProviderMode             | 2 bit int. 0=Not applicable, 1=Yes, 2=No                       |
| ustn         | 22         | GpcSegmentType                      | 2 bit int. Value is 1                                          |
| ustn         | 22         | GpcSegmentIncluded                  | Boolean. Default is true                                       |
| ustn         | 22         | Gpc                                 | Boolean                                                        |

## Example Usage / Encoder / Decoder

[https://iabgpp.com](https://iabgpp.com)
