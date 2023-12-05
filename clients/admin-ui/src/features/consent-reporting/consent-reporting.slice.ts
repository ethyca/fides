import { baseApi } from "~/features/common/api.slice";

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
          responseHandler: (response) => response.blob(),
        };
      },
      providesTags: ["Consent Reporting"],
      transformResponse: (data: Blob) => {
        const a = document.createElement("a");
        a.href = window.URL.createObjectURL(data);
        a.download = "consent-reports.csv";
        a.click();
      },
    }),
  }),
});

export const { useLazyDownloadReportQuery } = consentReportingApi;
