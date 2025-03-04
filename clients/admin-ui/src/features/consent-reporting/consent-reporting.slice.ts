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
      }
    >({
      query: (params) => ({
        url: "historical-privacy-preferences",
        params,
      }),
      providesTags: ["Consent Reporting"],
    }),
  }),
});

export const {
  useLazyDownloadReportQuery,
  useGetAllHistoricalPrivacyPreferencesQuery,
} = consentReportingApi;
