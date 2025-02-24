export var UsNatField;
(function (UsNatField) {
    UsNatField["VERSION"] = "Version";
    UsNatField["SHARING_NOTICE"] = "SharingNotice";
    UsNatField["SALE_OPT_OUT_NOTICE"] = "SaleOptOutNotice";
    UsNatField["SHARING_OPT_OUT_NOTICE"] = "SharingOptOutNotice";
    UsNatField["TARGETED_ADVERTISING_OPT_OUT_NOTICE"] = "TargetedAdvertisingOptOutNotice";
    UsNatField["SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE"] = "SensitiveDataProcessingOptOutNotice";
    UsNatField["SENSITIVE_DATA_LIMIT_USE_NOTICE"] = "SensitiveDataLimitUseNotice";
    UsNatField["SALE_OPT_OUT"] = "SaleOptOut";
    UsNatField["SHARING_OPT_OUT"] = "SharingOptOut";
    UsNatField["TARGETED_ADVERTISING_OPT_OUT"] = "TargetedAdvertisingOptOut";
    UsNatField["SENSITIVE_DATA_PROCESSING"] = "SensitiveDataProcessing";
    UsNatField["KNOWN_CHILD_SENSITIVE_DATA_CONSENTS"] = "KnownChildSensitiveDataConsents";
    UsNatField["PERSONAL_DATA_CONSENTS"] = "PersonalDataConsents";
    UsNatField["MSPA_COVERED_TRANSACTION"] = "MspaCoveredTransaction";
    UsNatField["MSPA_OPT_OUT_OPTION_MODE"] = "MspaOptOutOptionMode";
    UsNatField["MSPA_SERVICE_PROVIDER_MODE"] = "MspaServiceProviderMode";
    UsNatField["GPC_SEGMENT_TYPE"] = "GpcSegmentType";
    UsNatField["GPC_SEGMENT_INCLUDED"] = "GpcSegmentIncluded";
    UsNatField["GPC"] = "Gpc";
})(UsNatField || (UsNatField = {}));
export const USNAT_CORE_SEGMENT_FIELD_NAMES = [
    UsNatField.VERSION,
    UsNatField.SHARING_NOTICE,
    UsNatField.SALE_OPT_OUT_NOTICE,
    UsNatField.SHARING_OPT_OUT_NOTICE,
    UsNatField.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
    UsNatField.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE,
    UsNatField.SENSITIVE_DATA_LIMIT_USE_NOTICE,
    UsNatField.SALE_OPT_OUT,
    UsNatField.SHARING_OPT_OUT,
    UsNatField.TARGETED_ADVERTISING_OPT_OUT,
    UsNatField.SENSITIVE_DATA_PROCESSING,
    UsNatField.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
    UsNatField.PERSONAL_DATA_CONSENTS,
    UsNatField.MSPA_COVERED_TRANSACTION,
    UsNatField.MSPA_OPT_OUT_OPTION_MODE,
    UsNatField.MSPA_SERVICE_PROVIDER_MODE,
];
export const USNAT_GPC_SEGMENT_FIELD_NAMES = [UsNatField.GPC_SEGMENT_TYPE, UsNatField.GPC];
