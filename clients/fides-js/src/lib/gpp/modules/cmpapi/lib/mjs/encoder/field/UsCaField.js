export var UsCaField;
(function (UsCaField) {
    UsCaField["VERSION"] = "Version";
    UsCaField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsCaField["SHARING_OPT_OUT_NOTICE"] = "SharingOptOutNotice";
    UsCaField["SENSITIVE_DATA_LIMIT_USE_NOTICE"] = "SensitiveDataLimitUseNotice";
    UsCaField["SALE_OPT_OUT"] = "SaleOptOut";
    UsCaField["SHARING_OPT_OUT"] = "SharingOptOut";
    UsCaField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsCaField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsCaField["PERSONAL_DATA_CONSENTS"] = "PersonalDataConsents";
    UsCaField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsCaField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsCaField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsCaField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsCaField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsCaField["GPC"] = "Gpc";
})(UsCaField || (UsCaField = {}));
export const USCA_CORE_SEGMENT_FIELD_NAMES = [
    UsCaField.VERSION,
    UsCaField.SALE_OPT_OUT_NOTICE,
    UsCaField.SHARING_OPT_OUT_NOTICE,
    UsCaField.SENSITIVE_DATA_LIMIT_USE_NOTICE,
    UsCaField.SALE_OPT_OUT,
    UsCaField.SHARING_OPT_OUT,
    UsCaField.SENSITIVE_DATA_PROCESSING,
    UsCaField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsCaField.PERSONAL_DATA_CONSENTS,
    UsCaField.MSPA_COVERED_TRANSACTION,
    UsCaField.MSPA_OPT_OUT_OPTION_MODE,
    UsCaField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USCA_GPC_SEGMENT_FIELD_NAMES = [UsCaField.GPC_SEGMENT_TYPE, UsCaField.GPC];
