export var UsMtField;
(function (UsMtField) {
    UsMtField["VERSION"] = "Version";
    UsMtField["SHARING_NOTICE"] = "SharingNotice";
    UsMtField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsMtField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsMtField["SALE_OPT_OUT"] = "SaleOptOut";
    UsMtField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsMtField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsMtField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsMtField["ADDITIONAL_DATA_PROCESSING_CONSENT"] = "AdditionalDataProcessingConsent";
    UsMtField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsMtField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsMtField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsMtField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsMtField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsMtField["GPC"] = "Gpc";
})(UsMtField || (UsMtField = {}));
export const USMT_CORE_SEGMENT_FIELD_NAMES = [
    UsMtField.VERSION,
    UsMtField.SHARING_NOTICE,
    UsMtField.SALE_OPT_OUT_NOTICE,
    UsMtField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsMtField.SALE_OPT_OUT,
    UsMtField.TARGETED_ADVERTISING_OPT_OUT,
    UsMtField.SENSITIVE_DATA_PROCESSING,
    UsMtField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsMtField.ADDITIONAL_DATA_PROCESSING_CONSENT,
    UsMtField.MSPA_COVERED_TRANSACTION,
    UsMtField.MSPA_OPT_OUT_OPTION_MODE,
    UsMtField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USMT_GPC_SEGMENT_FIELD_NAMES = [UsMtField.GPC_SEGMENT_TYPE, UsMtField.GPC];
