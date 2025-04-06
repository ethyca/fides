export var UsTnField;
(function (UsTnField) {
    UsTnField["VERSION"] = "Version";
    UsTnField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsTnField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsTnField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsTnField["SALE_OPT_OUT"] = "SaleOptOut";
    UsTnField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsTnField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsTnField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsTnField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsTnField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsTnField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsTnField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsTnField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsTnField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsTnField["GPC"] = "Gpc";
})(UsTnField || (UsTnField = {}));
export const USTN_CORE_SEGMENT_FIELD_NAMES = [
    UsTnField.VERSION,
    UsTnField.PROCESSING_NOTICE,
    UsTnField.SALE_OPT_OUT_NOTICE,
    UsTnField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsTnField.SALE_OPT_OUT,
    UsTnField.TARGETED_ADVERTISING_OPT_OUT,
    UsTnField.SENSITIVE_DATA_PROCESSING,
    UsTnField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsTnField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsTnField.MSPA_COVERED_TRANSACTION,
    UsTnField.MSPA_OPT_OUT_OPTION_MODE,
    UsTnField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USTN_GPC_SEGMENT_FIELD_NAMES = [UsTnField.GPC_SEGMENT_TYPE, UsTnField.GPC];
