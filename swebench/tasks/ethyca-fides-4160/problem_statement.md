## Description

We need to add developer-friendly TCF (Transparency and Consent Framework) information to the Privacy Experience API. When developers request privacy experiences with TCF overlays, they should be able to get pre-computed metadata that helps with implementing consent flows.

Additionally, the existing `tcf_util.py` module has grown too large and needs to be refactored into a proper `tcf` subpackage for better organization.

## Expected Behavior

### TCF Meta Information
- A new `include_meta` query parameter should be added to the privacy experience endpoint
- When `include_meta=True`, the response should include a `meta` object with:
  - `version_hash`: A hash representing the current TCF configuration (e.g., "75fb2dafef58")
  - `accept_all_tc_string`: Pre-computed TC string for accepting all consents
  - `accept_all_tc_mobile_data`: Mobile-formatted data for accepting all
  - `reject_all_tc_string`: Pre-computed TC string for rejecting all consents
  - `reject_all_tc_mobile_data`: Mobile-formatted data for rejecting all
- When TCF is disabled or no TCF contents exist, these meta fields should be empty/falsy

### TCModel Validation
A `TCModel` class is needed with the following validation rules:
- `cmp_id`: Must be non-negative (reject negative values)
- `vendor_list_version`: Must be non-negative
- `policy_version`: Must be non-negative
- `cmp_version`: Must be positive (greater than 0)
- `publisher_country_code`: Must be exactly 2 alphabetic characters, automatically uppercased
- `consent_language`: Must be converted to 2-letter uppercase code
- `purpose_legitimate_interests`: Must filter out purposes that cannot have legitimate interests (purposes 1, 3, 4, 5, 6)
- `vendor_consents` and `vendor_legitimate_interests`: Must filter vendors based on GVL rules

### TCFVersionHash Model
A model to track TCF experience versions with automatically sorted list fields for consistent hashing.

### Code Reorganization
- Move TCF-related utilities from `tcf_util.py` into a `tcf` subpackage
- `ConsentRecordType` and `get_tcf_contents` should be accessible from the new location

## Why This Matters

This feature makes it easier for developers to implement consent experiences on mobile apps and web clients. By providing pre-computed TC strings and mobile data in the API response, developers don't need to compute these values client-side, reducing complexity and potential implementation errors.
