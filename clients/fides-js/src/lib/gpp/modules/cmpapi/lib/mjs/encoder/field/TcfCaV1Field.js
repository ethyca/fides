export var TcfCaV1Field;
(function (TcfCaV1Field) {
    TcfCaV1Field["VERSION"] = "Version";
    TcfCaV1Field["CREATED"] = "Created";
    TcfCaV1Field["LAST_UPDATED"] = "LastUpdated";
    TcfCaV1Field["CMP_ID"] = "CmpId";
    TcfCaV1Field["CMP_VERSION"] = "CmpVersion";
    TcfCaV1Field["CONSENT_SCREEN"] = "ConsentScreen";
    TcfCaV1Field["CONSENT_LANGUAGE"] = "ConsentLanguage";
    TcfCaV1Field["VENDOR_LIST_VERSION"] = "VendorListVersion";
    TcfCaV1Field["TCF_POLICY_VERSION"] = "TcfPolicyVersion";
    TcfCaV1Field["USE_NON_STANDARD_STACKS"] = "UseNonStandardStacks";
    TcfCaV1Field["SPECIAL_FEATURE_EXPRESS_CONSENT"] = "SpecialFeatureExpressConsent";
    TcfCaV1Field["PUB_PURPOSES_SEGMENT_TYPE"] = "PubPurposesSegmentType";
    TcfCaV1Field["PURPOSES_EXPRESS_CONSENT"] = "PurposesExpressConsent";
    TcfCaV1Field["PURPOSES_IMPLIED_CONSENT"] = "PurposesImpliedConsent";
    TcfCaV1Field["VENDOR_EXPRESS_CONSENT"] = "VendorExpressConsent";
    TcfCaV1Field["VENDOR_IMPLIED_CONSENT"] = "VendorImpliedConsent";
    TcfCaV1Field["PUB_RESTRICTIONS"] = "PubRestrictions";
    TcfCaV1Field["PUB_PURPOSES_EXPRESS_CONSENT"] = "PubPurposesExpressConsent";
    TcfCaV1Field["PUB_PURPOSES_IMPLIED_CONSENT"] = "PubPurposesImpliedConsent";
    TcfCaV1Field["NUM_CUSTOM_PURPOSES"] = "NumCustomPurposes";
    TcfCaV1Field["CUSTOM_PURPOSES_EXPRESS_CONSENT"] = "CustomPurposesExpressConsent";
    TcfCaV1Field["CUSTOM_PURPOSES_IMPLIED_CONSENT"] = "CustomPurposesImpliedConsent";
    TcfCaV1Field["DISCLOSED_VENDORS_SEGMENT_TYPE"] = "DisclosedVendorsSegmentType";
    TcfCaV1Field["DISCLOSED_VENDORS"] = "DisclosedVendors";
})(TcfCaV1Field || (TcfCaV1Field = {}));
export const TCFCAV1_CORE_SEGMENT_FIELD_NAMES = [
    TcfCaV1Field.VERSION,
    TcfCaV1Field.CREATED,
    TcfCaV1Field.LAST_UPDATED,
    TcfCaV1Field.CMP_ID,
    TcfCaV1Field.CMP_VERSION,
    TcfCaV1Field.CONSENT_SCREEN,
    TcfCaV1Field.CONSENT_LANGUAGE,
    TcfCaV1Field.VENDOR_LIST_VERSION,
    TcfCaV1Field.TCF_POLICY_VERSION,
    TcfCaV1Field.USE_NON_STANDARD_STACKS,
    TcfCaV1Field.SPECIAL_FEATURE_EXPRESS_CONSENT,
    TcfCaV1Field.PURPOSES_EXPRESS_CONSENT,
    TcfCaV1Field.PURPOSES_IMPLIED_CONSENT,
    TcfCaV1Field.VENDOR_EXPRESS_CONSENT,
    TcfCaV1Field.VENDOR_IMPLIED_CONSENT,
    TcfCaV1Field.PUB_RESTRICTIONS,
];
export const TCFCAV1_PUBLISHER_PURPOSES_SEGMENT_FIELD_NAMES = [
    TcfCaV1Field.PUB_PURPOSES_SEGMENT_TYPE,
    TcfCaV1Field.PUB_PURPOSES_EXPRESS_CONSENT,
    TcfCaV1Field.PUB_PURPOSES_IMPLIED_CONSENT,
    TcfCaV1Field.NUM_CUSTOM_PURPOSES,
    TcfCaV1Field.CUSTOM_PURPOSES_EXPRESS_CONSENT,
    TcfCaV1Field.CUSTOM_PURPOSES_IMPLIED_CONSENT,
];
export const TCFCAV1_DISCLOSED_VENDORS_SEGMENT_FIELD_NAMES = [
    TcfCaV1Field.DISCLOSED_VENDORS_SEGMENT_TYPE,
    TcfCaV1Field.DISCLOSED_VENDORS,
];
