/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Pre-parsed GPP data and GPP string for a CMP SDK
 */
export type GPPMobileData = {
  /**
   * GPP version
   */
  IABGPP_HDR_Version: string;
  /**
   * List of section IDs
   */
  IABGPP_HDR_Sections: string;
  /**
   * Full consent string in its encoded form
   */
  IABGPP_HDR_GppString: string;
  /**
   * Section ID(s) considered to be in force. Multiple IDs are separated by underscores
   */
  IABGPP_GppSID: string;
};
