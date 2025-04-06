export var UsCoField;
(function (UsCoField) {
    UsCoField["VERSION"] = "Version";
    UsCoField["SHARING_NOTICE"] = "SharingNotice";
    UsCoField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsCoField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsCoField["SALE_OPT_OUT"] = "SaleOptOut";
    UsCoField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsCoField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsCoField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsCoField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsCoField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsCoField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsCoField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsCoField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsCoField["GPC"] = "Gpc";
})(UsCoField || (UsCoField = {}));
export const USCO_CORE_SEGMENT_FIELD_NAMES = [
    UsCoField.VERSION,
    UsCoField.SHARING_NOTICE,
    UsCoField.SALE_OPT_OUT_NOTICE,
    UsCoField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsCoField.SALE_OPT_OUT,
    UsCoField.TARGETED_ADVERTISING_OPT_OUT,
    UsCoField.SENSITIVE_DATA_PROCESSING,
    UsCoField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsCoField.MSPA_COVERED_TRANSACTION,
    UsCoField.MSPA_OPT_OUT_OPTION_MODE,
    UsCoField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USCO_GPC_SEGMENT_FIELD_NAMES = [UsCoField.GPC_SEGMENT_TYPE, UsCoField.GPC];
