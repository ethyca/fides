export type Infrastructure = "aws" | "okta";

/**
 * The credential strings must be obscured: zlib compressed and base64 encoded.
 * TODO: helper function for obscuring strings.
 */
export interface ScannerGenerateParams {
  organization_key: string;
  generate: {
    config: {
      /** Obscured */
      aws_secret_access_key: string;
      /** Obscured */
      aws_access_key_id: string;
      region_name: string;
    };
    target: Infrastructure;
    type: "systems";
  };
}

export interface ScannerGenerateResponse {
  generate_results: {}[];
}
