/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Pre-parsed TC data and TC string for a CMP SDK:
 *
 * https://github.com/InteractiveAdvertisingBureau/GDPR-Transparency-and-Consent-Framework/blob/master/TCFv2/IAB%20Tech%20Lab%20-%20CMP%20API%20v2.md#in-app-details
 */
export type TCMobileData = {
  /**
   * The unsigned integer ID of CMP SDK
   */
  IABTCF_CmpSdkID?: number;
  /**
   * The unsigned integer version number of CMP SDK
   */
  IABTCF_CmpSdkVersion?: number;
  /**
   * The unsigned integer representing the version of the TCF that these consents adhere to.
   */
  IABTCF_PolicyVersion?: number;
  /**
   * 1: GDPR applies in current context, 0 - GDPR does not apply in current context, None=undetermined
   */
  IABTCF_gdprApplies?: TCMobileData.IABTCF_gdprApplies;
  /**
   * Two-letter ISO 3166-1 alpha-2 code
   */
  IABTCF_PublisherCC?: string;
  /**
   * Vendors can use this value to determine whether consent for purpose one is required. 0: no special treatment. 1: purpose one not disclosed
   */
  IABTCF_PurposeOneTreatment?: TCMobileData.IABTCF_PurposeOneTreatment;
  /**
   * 1 - CMP uses customized stack descriptions and/or modified or supplemented standard illustrations.0 - CMP did not use a non-standard stack desc. and/or modified or supplemented Illustrations
   */
  IABTCF_UseNonStandardTexts?: TCMobileData.IABTCF_UseNonStandardTexts;
  /**
   * Fully encoded TC string
   */
  IABTCF_TCString?: string;
  /**
   * Binary string: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the consent status for Vendor ID n+1; false and true respectively. eg. '1' at index 0 is consent true for vendor ID 1
   */
  IABTCF_VendorConsents?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the legitimate interest status for Vendor ID n+1; false and true respectively. eg. '1' at index 0 is legitimate interest established true for vendor ID 1
   */
  IABTCF_VendorLegitimateInterests?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the consent status for purpose ID n+1; false and true respectively. eg. '1' at index 0 is consent true for purpose ID 1
   */
  IABTCF_PurposeConsents?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the legitimate interest status for purpose ID n+1; false and true respectively. eg. '1' at index 0 is legitimate interest established true for purpose ID 1
   */
  IABTCF_PurposeLegitimateInterests?: string;
  /**
   * Binary String: The '0' or '1' at position n – where n's indexing begins at 0 – indicates the opt-in status for special feature ID n+1; false and true respectively. eg. '1' at index 0 is opt-in true for special feature ID 1
   */
  IABTCF_SpecialFeaturesOptIns?: string;
  IABTCF_PublisherConsent?: string;
  IABTCF_PublisherLegitimateInterests?: string;
  IABTCF_PublisherCustomPurposesConsents?: string;
  IABTCF_PublisherCustomPurposesLegitimateInterests?: string;
  IABTCF_AddtlConsent?: string;
};

export namespace TCMobileData {

  /**
   * 1: GDPR applies in current context, 0 - GDPR does not apply in current context, None=undetermined
   */
  export enum IABTCF_gdprApplies {
    '_0' = 0,
    '_1' = 1,
  }

  /**
   * Vendors can use this value to determine whether consent for purpose one is required. 0: no special treatment. 1: purpose one not disclosed
   */
  export enum IABTCF_PurposeOneTreatment {
    '_0' = 0,
    '_1' = 1,
  }

  /**
   * 1 - CMP uses customized stack descriptions and/or modified or supplemented standard illustrations.0 - CMP did not use a non-standard stack desc. and/or modified or supplemented Illustrations
   */
  export enum IABTCF_UseNonStandardTexts {
    '_0' = 0,
    '_1' = 1,
  }


}

