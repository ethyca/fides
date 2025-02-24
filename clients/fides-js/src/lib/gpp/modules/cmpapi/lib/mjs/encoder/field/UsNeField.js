export var UsNeField;
(function (UsNeField) {
    UsNeField["VERSION"] = "Version";
    UsNeField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsNeField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsNeField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsNeField["SALE_OPT_OUT"] = "SaleOptOut";
    UsNeField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsNeField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsNeField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsNeField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsNeField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsNeField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsNeField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsNeField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsNeField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsNeField["GPC"] = "Gpc";
})(UsNeField || (UsNeField = {}));
export const USNE_CORE_SEGMENT_FIELD_NAMES = [
    UsNeField.VERSION,
    UsNeField.PROCESSING_NOTICE,
    UsNeField.SALE_OPT_OUT_NOTICE,
    UsNeField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsNeField.SALE_OPT_OUT,
    UsNeField.TARGETED_ADVERTISING_OPT_OUT,
    UsNeField.SENSITIVE_DATA_PROCESSING,
    UsNeField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsNeField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsNeField.MSPA_COVERED_TRANSACTION,
    UsNeField.MSPA_OPT_OUT_OPTION_MODE,
    UsNeField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USNE_GPC_SEGMENT_FIELD_NAMES = [UsNeField.GPC_SEGMENT_TYPE, UsNeField.GPC];
