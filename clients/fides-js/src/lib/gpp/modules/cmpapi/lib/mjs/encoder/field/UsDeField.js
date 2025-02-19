export var UsDeField;
(function (UsDeField) {
    UsDeField["VERSION"] = "Version";
    UsDeField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsDeField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsDeField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsDeField["SALE_OPT_OUT"] = "SaleOptOut";
    UsDeField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsDeField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsDeField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsDeField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsDeField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsDeField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsDeField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsDeField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsDeField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsDeField["GPC"] = "Gpc";
})(UsDeField || (UsDeField = {}));
export const USDE_CORE_SEGMENT_FIELD_NAMES = [
    UsDeField.VERSION,
    UsDeField.PROCESSING_NOTICE,
    UsDeField.SALE_OPT_OUT_NOTICE,
    UsDeField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsDeField.SALE_OPT_OUT,
    UsDeField.TARGETED_ADVERTISING_OPT_OUT,
    UsDeField.SENSITIVE_DATA_PROCESSING,
    UsDeField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsDeField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsDeField.MSPA_COVERED_TRANSACTION,
    UsDeField.MSPA_OPT_OUT_OPTION_MODE,
    UsDeField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USDE_GPC_SEGMENT_FIELD_NAMES = [UsDeField.GPC_SEGMENT_TYPE, UsDeField.GPC];
