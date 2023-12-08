import {
  UsCaV1,
  UsCaV1Field,
  UsCoV1,
  UsCoV1Field,
  UsCtV1,
  UsCtV1Field,
  UsNatV1,
  UsNatV1Field,
  UsUtV1,
  UsUtV1Field,
  UsVaV1,
  UsVaV1Field,
} from "@iabgpp/cmpapi";

export const SUPPORTED_APIS = ["2:tcfeuv2"];

interface GppFields {
  gpp_notice_fields: string[];
  gpp_mechanism_fields: string[];
}
type FidesRegionToGppFields = Record<string, GppFields>;
type NoticeKeyToFidesRegionGppFields = Record<string, FidesRegionToGppFields>;

/**
 * Eventually this will be encoded on the privacy notice itself
 *
 * Currently based off of this table
 * https://ethyca.atlassian.net/wiki/spaces/EN/pages/2852945989/2023-11-30+Fides.js+GPP+implementation?focusedCommentId=2861989902
 */
export const NOTICE_KEY_TO_FIDES_REGION_GPP_FIELDS: NoticeKeyToFidesRegionGppFields =
  {
    sales_sharing_targeted_advertising: {
      us: {
        gpp_notice_fields: [
          UsNatV1Field.SALE_OPT_OUT_NOTICE,
          UsNatV1Field.SHARING_OPT_OUT_NOTICE,
          UsNatV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
          UsNatV1Field.SHARING_NOTICE,
        ],
        gpp_mechanism_fields: [
          UsNatV1Field.SALE_OPT_OUT,
          UsNatV1Field.SHARING_OPT_OUT,
          UsNatV1Field.TARGETED_ADVERTISING_OPT_OUT,
        ],
      },
    },
    data_sales_and_sharing: {
      us_ca: {
        gpp_notice_fields: [
          UsCaV1Field.SALE_OPT_OUT_NOTICE,
          UsCaV1Field.SHARING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          UsCaV1Field.SALE_OPT_OUT,
          UsCaV1Field.SHARING_OPT_OUT,
        ],
      },
    },
    targeted_advertising: {
      us_co: {
        gpp_notice_fields: [
          UsCoV1Field.SALE_OPT_OUT_NOTICE,
          UsCoV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          UsCoV1Field.SALE_OPT_OUT,
          UsCoV1Field.TARGETED_ADVERTISING_OPT_OUT,
        ],
      },
      us_ct: {
        gpp_notice_fields: [UsCtV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [UsCtV1Field.TARGETED_ADVERTISING_OPT_OUT],
      },
      us_ut: {
        gpp_notice_fields: [UsUtV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [UsUtV1Field.TARGETED_ADVERTISING_OPT_OUT],
      },
      us_va: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
      us_ia: {
        // DEFER: Iowa isn't part of the GPP spec yet
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
    },
    data_sharing: {
      us_ut: {
        gpp_notice_fields: [UsUtV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_va: {
        gpp_notice_fields: [UsVaV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_co: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
      us_ct: {
        gpp_notice_fields: [UsCtV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
    },
    data_sales: {
      us_co: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
      us_ct: {
        gpp_notice_fields: [UsCtV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [UsCtV1Field.SALE_OPT_OUT],
      },
      us_ut: {
        gpp_notice_fields: [UsUtV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [UsUtV1Field.SALE_OPT_OUT],
      },
      us_va: {
        gpp_notice_fields: [UsVaV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [UsVaV1Field.SALE_OPT_OUT],
      },
      us_ia: {
        // DEFER: Iowa isn't part of the GPP spec yet
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
    },
    sensitive_personal_data_sharing: {
      us_ca: {
        gpp_notice_fields: [UsCaV1Field.SENSITIVE_DATA_LIMIT_USE_NOTICE],
        gpp_mechanism_fields: [
          UsCaV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
          UsCaV1Field.PERSONAL_DATA_CONSENTS,
        ],
      },
      us_ut: {
        gpp_notice_fields: [
          UsUtV1Field.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          UsUtV1Field.SENSITIVE_DATA_PROCESSING,
          UsUtV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
        ],
      },
      us_va: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          UsVaV1Field.SENSITIVE_DATA_PROCESSING,
          UsVaV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
        ],
      },
      us_co: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          UsCoV1Field.SENSITIVE_DATA_PROCESSING,
          UsCoV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
        ],
      },
      us_ct: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          UsCtV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
          UsCtV1Field.SENSITIVE_DATA_PROCESSING,
        ],
      },
    },
  };

export const FIDES_REGION_TO_GPP_SECTION_ID: Record<string, number> = {
  us: UsNatV1.ID,
  us_ca: UsCaV1.ID,
  us_ct: UsCtV1.ID,
  us_co: UsCoV1.ID,
  us_ut: UsUtV1.ID,
  us_va: UsVaV1.ID,
  // DEFER: Iowa isn't part of the GPP spec yet
};
