import { Dayjs } from "dayjs";

import { baseApi } from "~/features/common/api.slice";
import {
  ConditionalTotalPage_ConsentReportingSchema_,
  PreferencesSavedExtended,
} from "~/types/api";
import {
  DateRangeParams,
  PaginatedResponse,
  PaginationQueryParams,
} from "~/types/query-params";

export interface TCFVersionHashHistoryResponse {
  id: string;
  tcf_configuration_id?: string | null;
  previous_hash?: string | null;
  current_hash: string;
  changed_at: string;
  trigger_source: string;
}

const startOfDayIso = (date?: Dayjs | null) =>
  date?.startOf("day")?.utc()?.toISOString();

const endOfDayIso = (date?: Dayjs | null) =>
  date?.endOf("day")?.utc()?.toISOString();

export const consentReportingApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getCurrentPrivacyPreferences: build.query<
      PreferencesSavedExtended,
      { search: string }
    >({
      query: ({ search }) => ({
        url: "current-privacy-preferences",
        params: {
          email: search,
          phone_number: search,
          fides_user_device_id: search,
          external_id: search,
        },
      }),
      providesTags: ["Current Privacy Preferences"],
    }),

    downloadReport: build.query<any, DateRangeParams>({
      query: ({ startDate, endDate }) => {
        const params = {
          created_gt: startOfDayIso(startDate),
          created_lt: endOfDayIso(endDate),
          download_csv: "true",
        };
        return {
          url: "plus/consent_reporting",
          params,
          responseHandler: "content-type",
        };
      },
      providesTags: ["Consent Reporting Export"],
    }),
    getAllHistoricalPrivacyPreferences: build.query<
      ConditionalTotalPage_ConsentReportingSchema_,
      PaginationQueryParams & DateRangeParams & { includeTotal?: boolean }
    >({
      query: ({ page, size, startDate, endDate, includeTotal = true }) => {
        return {
          url: "historical-privacy-preferences",
          params: {
            page,
            size,
            request_timestamp_gt: startOfDayIso(startDate),
            request_timestamp_lt: endOfDayIso(endDate),
            include_total: includeTotal,
          },
        };
      },
      providesTags: ["Consent Reporting"],
    }),
    getTCFVersionHistory: build.query<
      PaginatedResponse<TCFVersionHashHistoryResponse>,
      PaginationQueryParams
    >({
      query: ({ page, size }) => ({
        url: "privacy-experience/history",
        params: { page, size },
      }),
      providesTags: ["TCF Version History"],
    }),
  }),
});

export const {
  useLazyDownloadReportQuery,
  useGetAllHistoricalPrivacyPreferencesQuery,
  useLazyGetCurrentPrivacyPreferencesQuery,
  useGetTCFVersionHistoryQuery,
} = consentReportingApi;
