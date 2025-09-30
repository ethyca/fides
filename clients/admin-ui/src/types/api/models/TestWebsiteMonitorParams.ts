/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

/**
 * Configuration parameters for the test website monitor
 */
export type TestWebsiteMonitorParams = {
  /**
   * The locations from which the website should be monitored
   */
  locations?: Array<string> | null;
  /**
   * List of domains to exclude from monitoring
   */
  exclude_domains?: Array<string> | null;
  /**
   * URL to a sitemap.xml file that will be used to discover pages to monitor
   */
  sitemap_url?: string | null;
  /**
   * Number of test cookies to generate
   */
  num_cookies?: number;
  /**
   * Number of test JavaScript requests to generate
   */
  num_javascript_requests?: number;
  /**
   * Number of test image requests to generate
   */
  num_image_requests?: number;
  /**
   * Number of test iframe requests to generate
   */
  num_iframe_requests?: number;
  /**
   * Number of general browser requests to generate
   */
  num_browser_requests?: number;
  /**
   * List of test domains to use in generated assets
   */
  test_domains?: Array<string>;
  /**
   * List of test pages where assets are discovered
   */
  test_pages?: Array<string>;
  /**
   * List of test locations for asset discovery
   */
  test_locations?: Array<string>;
  /**
   * Percentage of assets that should be generated with granted consent (0.0 to 1.0)
   */
  consent_granted_percentage?: number;
  /**
   * Percentage of assets that should be generated with denied consent (0.0 to 1.0)
   */
  consent_denied_percentage?: number;
  /**
   * Percentage of assets that should be generated with cmp_error consent (0.0 to 1.0)
   */
  consent_cmp_error_percentage?: number;
  /**
   * Sample cookie names to use
   */
  cookie_names?: Array<string>;
  /**
   * Sample cookie values to use
   */
  cookie_values?: Array<string>;
  /**
   * Percentage of assets that should be matched to vendors (0.0 to 1.0)
   */
  vendor_match_percentage?: number;
  /**
   * List of test vendor IDs to assign to matched assets
   */
  test_vendor_ids?: Array<string>;
  /**
   * Experiences data for consent notice mapping. Uses default experiences data if not provided.
   */
  experiences_data?: Record<string, any>;
};
