/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type CreateExportPrivacyPreferencesJobRequest = {
  /**
   * The destination URL to export to (i.e s3://target-bucket/prefix)
   */
  destination_url: string;
  /**
   * Batch size for exports (1-1000); default is 100
   */
  batch_size?: number;
};
