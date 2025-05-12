export var UsOrField;
(function (UsOrField) {
    UsOrField["VERSION"] = "Version";
    UsOrField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsOrField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsOrField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsOrField["SALE_OPT_OUT"] = "SaleOptOut";
    UsOrField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsOrField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsOrField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsOrField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsOrField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsOrField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsOrField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsOrField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsOrField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsOrField["GPC"] = "Gpc";
})(UsOrField || (UsOrField = {}));
export const USOR_CORE_SEGMENT_FIELD_NAMES = [
    UsOrField.VERSION,
    UsOrField.PROCESSING_NOTICE,
    UsOrField.SALE_OPT_OUT_NOTICE,
    UsOrField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsOrField.SALE_OPT_OUT,
    UsOrField.TARGETED_ADVERTISING_OPT_OUT,
    UsOrField.SENSITIVE_DATA_PROCESSING,
    UsOrField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsOrField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsOrField.MSPA_COVERED_TRANSACTION,
    UsOrField.MSPA_OPT_OUT_OPTION_MODE,
    UsOrField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USOR_GPC_SEGMENT_FIELD_NAMES = [UsOrField.GPC_SEGMENT_TYPE, UsOrField.GPC];
