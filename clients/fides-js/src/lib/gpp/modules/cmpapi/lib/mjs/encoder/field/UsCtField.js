export var UsCtField;
(function (UsCtField) {
    UsCtField["VERSION"] = "Version";
    UsCtField["SHARING_NOTICE"] = "SharingNotice";
    UsCtField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsCtField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsCtField["SALE_OPT_OUT"] = "SaleOptOut";
    UsCtField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsCtField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsCtField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsCtField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsCtField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsCtField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsCtField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsCtField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsCtField["GPC"] = "Gpc";
})(UsCtField || (UsCtField = {}));
export const USCT_CORE_SEGMENT_FIELD_NAMES = [
    UsCtField.VERSION,
    UsCtField.SHARING_NOTICE,
    UsCtField.SALE_OPT_OUT_NOTICE,
    UsCtField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsCtField.SALE_OPT_OUT,
    UsCtField.TARGETED_ADVERTISING_OPT_OUT,
    UsCtField.SENSITIVE_DATA_PROCESSING,
    UsCtField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsCtField.MSPA_COVERED_TRANSACTION,
    UsCtField.MSPA_OPT_OUT_OPTION_MODE,
    UsCtField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USCT_GPC_SEGMENT_FIELD_NAMES = [UsCtField.GPC_SEGMENT_TYPE, UsCtField.GPC];
