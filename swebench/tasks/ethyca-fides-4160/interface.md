Type: Class
Name: TCModel
Location: fides/api/util/tcf/tc_model.py
Description: Pydantic model representing a Transparency & Consent (TC) model for IAB TCF 2.0 compliance. Must be importable from fides.api.util.tcf.tc_string as well. Contains validated fields for CMP information, consent data, vendor information, and purpose selections with the following validation rules:
- cmp_id: NonNegativeInt field, raises ValidationError for negative values, can coerce from string/float to int
- vendor_list_version: NonNegativeInt field, can coerce from string/float
- policy_version: NonNegativeInt field, can coerce from string/float
- cmp_version: PositiveInt field (must be >= 1), raises ValidationError for 0 or negative
- publisher_country_code: Must be exactly 2 alphabetic characters, auto-uppercases (e.g., "aa" -> "AA"), raises ValidationError for non-alpha or wrong length (e.g., "USA", "^^")
- consent_language: Returns first 2 uppercase letters of input (e.g., "English" -> "EN")
- purpose_legitimate_interests: Validator must filter out purposes 1, 3, 4, 5, 6 (input [1,2,3,4,7] becomes [2,7])
- vendor_consents: Root validator filters vendors that have no consent purposes in GVL
- vendor_legitimate_interests: Root validator filters vendors based on GVL rules (keeps vendors with legIntPurposes or specialPurposes, filters others)
- is_service_specific: Boolean field affecting vendor filtering behavior

Type: Class
Name: TCFVersionHash
Location: fides/api/util/tcf/experience_meta.py
Description: Pydantic model that stores TCF experience version information used to generate a hash. All list fields must be automatically sorted in ascending order via a root_validator.
Signature: Fields: policy_version (int), purpose_consents (List[int] sorted ascending), purpose_legitimate_interests (List[int] sorted ascending), special_feature_optins (List[int] sorted ascending), vendor_consents (List[int] sorted ascending), vendor_legitimate_interests (List[int] sorted ascending)

Type: Function
Name: _build_tcf_version_hash_model
Location: fides/api/util/tcf/experience_meta.py
Description: Builds a TCFVersionHash model from TCFExperienceContents.
Signature: _build_tcf_version_hash_model(tcf_contents: TCFExperienceContents) -> TCFVersionHash

Type: Function
Name: build_tcf_version_hash
Location: fides/api/util/tcf/experience_meta.py
Description: Returns a 12-character version hash string for TCF contents.
Signature: build_tcf_version_hash(tcf_contents: TCFExperienceContents) -> str

Type: Function
Name: get_tcf_contents
Location: fides/api/util/tcf/tcf_experience_contents.py
Description: Retrieves TCF experience contents from the database.
Signature: get_tcf_contents(db: Session) -> TCFExperienceContents

Type: Class
Name: ConsentRecordType
Location: fides/api/util/tcf/tcf_experience_contents.py
Description: Enum or type representing consent record types. Moved from tcf_util module.

Type: Constant
Name: CMP_ID
Location: fides/api/util/tcf/tc_model.py
Description: Integer constant representing the CMP ID, set to 12.
