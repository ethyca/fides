/* istanbul ignore file */
/* tslint:disable */

/**
 * Specifies fields provided to the AES Decryption endpoint
 */
export type AesDecryptionRequest = {
  value: string;
  key: string;
  nonce: string;
};
