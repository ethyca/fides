export var UsTxField;
(function (UsTxField) {
    UsTxField["VERSION"] = "Version";
    UsTxField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsTxField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsTxField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsTxField["SALE_OPT_OUT"] = "SaleOptOut";
    UsTxField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsTxField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsTxField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsTxField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsTxField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsTxField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsTxField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsTxField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsTxField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsTxField["GPC"] = "Gpc";
})(UsTxField || (UsTxField = {}));
export const USTX_CORE_SEGMENT_FIELD_NAMES = [
    UsTxField.VERSION,
    UsTxField.PROCESSING_NOTICE,
    UsTxField.SALE_OPT_OUT_NOTICE,
    UsTxField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsTxField.SALE_OPT_OUT,
    UsTxField.TARGETED_ADVERTISING_OPT_OUT,
    UsTxField.SENSITIVE_DATA_PROCESSING,
    UsTxField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsTxField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsTxField.MSPA_COVERED_TRANSACTION,
    UsTxField.MSPA_OPT_OUT_OPTION_MODE,
    UsTxField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USTX_GPC_SEGMENT_FIELD_NAMES = [UsTxField.GPC_SEGMENT_TYPE, UsTxField.GPC];
