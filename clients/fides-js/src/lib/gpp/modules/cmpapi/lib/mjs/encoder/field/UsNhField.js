export var UsNhField;
(function (UsNhField) {
    UsNhField["VERSION"] = "Version";
    UsNhField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsNhField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsNhField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsNhField["SALE_OPT_OUT"] = "SaleOptOut";
    UsNhField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsNhField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsNhField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsNhField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsNhField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsNhField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsNhField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsNhField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsNhField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsNhField["GPC"] = "Gpc";
})(UsNhField || (UsNhField = {}));
export const USNH_CORE_SEGMENT_FIELD_NAMES = [
    UsNhField.VERSION,
    UsNhField.PROCESSING_NOTICE,
    UsNhField.SALE_OPT_OUT_NOTICE,
    UsNhField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsNhField.SALE_OPT_OUT,
    UsNhField.TARGETED_ADVERTISING_OPT_OUT,
    UsNhField.SENSITIVE_DATA_PROCESSING,
    UsNhField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsNhField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsNhField.MSPA_COVERED_TRANSACTION,
    UsNhField.MSPA_OPT_OUT_OPTION_MODE,
    UsNhField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USNH_GPC_SEGMENT_FIELD_NAMES = [UsNhField.GPC_SEGMENT_TYPE, UsNhField.GPC];
