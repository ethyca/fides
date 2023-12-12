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

interface GppMechanismField {
  field: string;
  not_available: number | number[];
  opt_out: number | number[];
  not_opt_out: number | number[];
}
interface GppFields {
  gpp_notice_fields: string[];
  gpp_mechanism_fields: GppMechanismField[];
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
    data_sales_and_sharing: {
      // QUESTION: should national be here AND in "data_sales" + "data_sharing"
      us: {
        gpp_notice_fields: [
          UsNatV1Field.SALE_OPT_OUT_NOTICE,
          UsNatV1Field.SHARING_OPT_OUT_NOTICE,
          UsNatV1Field.SHARING_NOTICE,
        ],
        gpp_mechanism_fields: [
          {
            field: UsNatV1Field.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
          {
            field: UsNatV1Field.SHARING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ca: {
        gpp_notice_fields: [
          UsCaV1Field.SALE_OPT_OUT_NOTICE,
          UsCaV1Field.SHARING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          {
            field: UsCaV1Field.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
          {
            field: UsCaV1Field.SHARING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
    },
    targeted_advertising: {
      us: {
        gpp_notice_fields: [UsNatV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsNatV1Field.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_co: {
        gpp_notice_fields: [UsCoV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsCoV1Field.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [UsCtV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsCtV1Field.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [UsUtV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsUtV1Field.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [UsVaV1Field.TARGETED_ADVERTISING_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsVaV1Field.TARGETED_ADVERTISING_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ia: {
        // DEFER: Iowa isn't part of the GPP spec yet
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
    },
    data_sharing: {
      // See question above: L34
      //   us: {
      //     gpp_notice_fields: [UsNatV1Field.SHARING_NOTICE],
      //     gpp_mechanism_fields: [],
      //   },
      us_ut: {
        gpp_notice_fields: [UsUtV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_va: {
        gpp_notice_fields: [UsVaV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_co: {
        gpp_notice_fields: [UsCoV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
      us_ct: {
        gpp_notice_fields: [UsCtV1Field.SHARING_NOTICE],
        gpp_mechanism_fields: [],
      },
    },
    data_sales: {
      // See question above: L34
      //   us: {
      //     gpp_notice_fields: [UsNatV1Field.SALE_OPT_OUT_NOTICE],
      //     gpp_mechanism_fields: [UsNatV1Field.SALE_OPT_OUT],
      //   },
      us_co: {
        gpp_notice_fields: [UsCoV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsCoV1Field.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [UsCtV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsCtV1Field.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [UsUtV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsUtV1Field.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [UsVaV1Field.SALE_OPT_OUT_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsVaV1Field.SALE_OPT_OUT,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ia: {
        // DEFER: Iowa isn't part of the GPP spec yet
        gpp_notice_fields: [],
        gpp_mechanism_fields: [],
      },
    },
    sensitive_personal_data_sharing: {
      us: {
        gpp_notice_fields: [
          UsNatV1Field.SENSITIVE_DATA_LIMIT_USE_NOTICE,
          UsNatV1Field.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          {
            field: UsNatV1Field.SENSITIVE_DATA_PROCESSING,
            not_available: Array(12).fill(0),
            opt_out: Array(12).fill(1),
            not_opt_out: Array(12).fill(2),
          },
          {
            field: UsNatV1Field.PERSONAL_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
          {
            field: UsNatV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: Array(2).fill(0),
            opt_out: Array(2).fill(1),
            not_opt_out: Array(2).fill(2),
          },
        ],
      },
      us_ca: {
        gpp_notice_fields: [UsCaV1Field.SENSITIVE_DATA_LIMIT_USE_NOTICE],
        gpp_mechanism_fields: [
          {
            field: UsCaV1Field.SENSITIVE_DATA_PROCESSING,
            not_available: Array(9).fill(0),
            opt_out: Array(9).fill(1),
            not_opt_out: Array(9).fill(2),
          },
          {
            field: UsCaV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: Array(2).fill(0),
            opt_out: Array(2).fill(1),
            not_opt_out: Array(2).fill(2),
          },
          {
            field: UsCaV1Field.PERSONAL_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ut: {
        gpp_notice_fields: [
          UsUtV1Field.SENSITIVE_DATA_PROCESSING_OPT_OUT_NOTICE,
        ],
        gpp_mechanism_fields: [
          {
            field: UsUtV1Field.SENSITIVE_DATA_PROCESSING,
            not_available: Array(8).fill(0),
            opt_out: Array(8).fill(1),
            not_opt_out: Array(8).fill(2),
          },
          {
            field: UsUtV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_va: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: UsVaV1Field.SENSITIVE_DATA_PROCESSING,
            not_available: Array(8).fill(0),
            opt_out: Array(8).fill(1),
            not_opt_out: Array(8).fill(2),
          },
          {
            field: UsVaV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_co: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: UsCoV1Field.SENSITIVE_DATA_PROCESSING,
            not_available: Array(7).fill(0),
            opt_out: Array(7).fill(1),
            not_opt_out: Array(7).fill(2),
          },
          {
            field: UsCoV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: 0,
            opt_out: 1,
            not_opt_out: 2,
          },
        ],
      },
      us_ct: {
        gpp_notice_fields: [],
        gpp_mechanism_fields: [
          {
            field: UsCtV1Field.KNOWN_CHILD_SENSITIVE_DATA_CONSENTS,
            not_available: Array(3).fill(0),
            opt_out: Array(3).fill(1),
            not_opt_out: Array(3).fill(2),
          },
          {
            field: UsCtV1Field.SENSITIVE_DATA_PROCESSING,
            not_available: Array(8).fill(0),
            opt_out: Array(8).fill(1),
            not_opt_out: Array(8).fill(2),
          },
        ],
      },
    },
  };

export const FIDES_REGION_TO_GPP_SECTION: Record<
  string,
  { name: string; id: number; prefix: string }
> = {
  us: { name: UsNatV1.NAME, id: UsNatV1.ID, prefix: "usnat" },
  us_ca: { name: UsCaV1.NAME, id: UsCaV1.ID, prefix: "usca" },
  us_ct: { name: UsCtV1.NAME, id: UsCtV1.ID, prefix: "usct" },
  us_co: { name: UsCoV1.NAME, id: UsCoV1.ID, prefix: "usco" },
  us_ut: { name: UsUtV1.NAME, id: UsUtV1.ID, prefix: "usut" },
  us_va: { name: UsVaV1.NAME, id: UsVaV1.ID, prefix: "usva" },
  // DEFER: Iowa isn't part of the GPP spec yet
};
