export var UsIaField;
(function (UsIaField) {
    UsIaField["VERSION"] = "Version";
    UsIaField["PROCESSING_NOTICE"] = "ProcessingNotice";
    UsIaField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsIaField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsIaField["SENSITIVE_DATA_OPT_OUT_NOTICE"] = "SensitiveDataOptOutNotice";
    UsIaField["SALE_OPT_OUT"] = "SaleOptOut";
    UsIaField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsIaField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsIaField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsIaField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsIaField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsIaField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsIaField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsIaField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsIaField["GPC"] = "Gpc";
})(UsIaField || (UsIaField = {}));
export const USIA_CORE_SEGMENT_FIELD_NAMES = [
    UsIaField.VERSION,
    UsIaField.PROCESSING_NOTICE,
    UsIaField.SALE_OPT_OUT_NOTICE,
    UsIaField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsIaField.SENSITIVE_DATA_OPT_OUT_NOTICE,
    UsIaField.SALE_OPT_OUT,
    UsIaField.TARGETED_ADVERTISING_OPT_OUT,
    UsIaField.SENSITIVE_DATA_PROCESSING,
    UsIaField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsIaField.MSPA_COVERED_TRANSACTION,
    UsIaField.MSPA_OPT_OUT_OPTION_MODE,
    UsIaField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USIA_GPC_SEGMENT_FIELD_NAMES = [UsIaField.GPC_SEGMENT_TYPE, UsIaField.GPC];
