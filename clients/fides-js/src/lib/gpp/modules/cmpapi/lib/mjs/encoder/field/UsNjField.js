export var UsNjField;
(function (UsNjField) {
    UsNjField["VERSION"] = "Version";
    UsNjField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsNjField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsNjField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsNjField["SALE_OPT_OUT"] = "SaleOptOut";
    UsNjField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsNjField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsNjField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsNjField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsNjField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsNjField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsNjField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsNjField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsNjField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsNjField["GPC"] = "Gpc";
})(UsNjField || (UsNjField = {}));
export const USNJ_CORE_SEGMENT_FIELD_NAMES = [
    UsNjField.VERSION,
    UsNjField.PROCESSING_NOTICE,
    UsNjField.SALE_OPT_OUT_NOTICE,
    UsNjField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsNjField.SALE_OPT_OUT,
    UsNjField.TARGETED_ADVERTISING_OPT_OUT,
    UsNjField.SENSITIVE_DATA_PROCESSING,
    UsNjField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsNjField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsNjField.MSPA_COVERED_TRANSACTION,
    UsNjField.MSPA_OPT_OUT_OPTION_MODE,
    UsNjField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USNJ_GPC_SEGMENT_FIELD_NAMES = [UsNjField.GPC_SEGMENT_TYPE, UsNjField.GPC];
