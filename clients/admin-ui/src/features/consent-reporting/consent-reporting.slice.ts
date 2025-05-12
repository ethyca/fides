import { Dayjs } from "dayjs";

import { baseApi } from "~/features/common/api.slice";
import {
  Page_ConsentReportingSchema_,
  PreferencesSavedExtended,
} from "~/types/api";
import { DateRange } from "~/types/common/DateRange";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

const startOfDayIso = (date?: Dayjs | null) =>
  date?.utc()?.startOf("day").toISOString();

const endOfDayIso = (date?: Dayjs | null) =>
  date?.utc()?.endOf("day").toISOString();

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

    downloadReport: build.query<any, DateRange>({
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
      Page_ConsentReportingSchema_,
      PaginationQueryParams & DateRange
    >({
      query: ({ page, size, startDate, endDate }) => {
        return {
          url: "historical-privacy-preferences",
          params: {
            page,
            size,
            request_timestamp_gt: startOfDayIso(startDate),
            request_timestamp_lt: endOfDayIso(endDate),
          },
        };
      },
      providesTags: ["Consent Reporting"],
    }),
  }),
});

export const {
  useLazyDownloadReportQuery,
  useGetAllHistoricalPrivacyPreferencesQuery,
  useLazyGetCurrentPrivacyPreferencesQuery,
} = consentReportingApi;
