import { baseApi } from "~/features/common/api.slice";
import { Page_ConsentReportingSchema_ } from "~/types/api";

type DateRange = {
  startDate?: string;
  endDate?: string;
};

export function convertDateRangeToSearchParams({
  startDate,
  endDate,
}: DateRange) {
  let startDateISO;
  if (startDate) {
    startDateISO = new Date(startDate);
    startDateISO.setUTCHours(0, 0, 0);
  }

  let endDateISO;
  if (endDate) {
    endDateISO = new Date(endDate);
    endDateISO.setUTCHours(0, 0, 0);
  }

  return {
    ...(startDateISO ? { created_gt: startDateISO.toISOString() } : {}),
    ...(endDateISO ? { created_lt: endDateISO.toISOString() } : {}),
  };
}

export const consentReportingApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getCurrentPrivacyPreferences: build.query<any, { search: string }>({
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
          ...convertDateRangeToSearchParams({ startDate, endDate }),
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
      {
        page: number;
        size: number;
      } & DateRange
    >({
      query: ({ page, size, startDate, endDate }) => ({
        url: "historical-privacy-preferences",
        params: {
          page,
          size,
          ...convertDateRangeToSearchParams({ startDate, endDate }),
        },
      }),
      providesTags: ["Consent Reporting"],
    }),
  }),
});

export const {
  useLazyDownloadReportQuery,
  useGetAllHistoricalPrivacyPreferencesQuery,
  useLazyGetCurrentPrivacyPreferencesQuery,
} = consentReportingApi;
