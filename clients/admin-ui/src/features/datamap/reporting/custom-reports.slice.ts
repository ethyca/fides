import { baseApi } from "~/features/common/api.slice";
import {
  CustomReportCreate,
  CustomReportResponse,
  Page_CustomReportResponseMinimal_,
} from "~/types/api";

// API endpoints
const customReportsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getMinimalCustomReports: build.query<
      Page_CustomReportResponseMinimal_,
      {
        pageIndex?: number;
        pageSize?: number;
      }
    >({
      query: ({ pageIndex = 1, pageSize = 50 }) => {
        const queryString = `page=${pageIndex}&size=${pageSize}`;
        return {
          url: `plus/custom-reports/minimal?${queryString}`,
        };
      },
      providesTags: ["Custom Reports"],
    }),
    getCustomReportById: build.query<CustomReportResponse, string>({
      query: (id) => ({ url: `plus/custom-report/${id}` }),
      providesTags: (_result, _error, arg) => [
        { type: "Custom Reports", id: arg },
      ],
    }),
    postCustomReport: build.mutation<CustomReportResponse, CustomReportCreate>({
      query: (payload) => ({
        method: "POST",
        url: "plus/custom-report",
        body: payload,
      }),
      invalidatesTags: ["Custom Reports"],
    }),
    deleteCustomReport: build.mutation<void, string>({
      query: (id) => ({
        method: "DELETE",
        url: `plus/custom-report/${id}`,
      }),
      invalidatesTags: ["Custom Reports"],
    }),
  }),
});

export const {
  useGetMinimalCustomReportsQuery,
  useLazyGetCustomReportByIdQuery,
  usePostCustomReportMutation,
  useDeleteCustomReportMutation,
} = customReportsApi;
