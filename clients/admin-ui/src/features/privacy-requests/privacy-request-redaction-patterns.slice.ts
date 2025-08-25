import { baseApi } from "~/features/common/api.slice";

export interface PrivacyRequestRedactionPatternsRequest {
  patterns: string[];
}

export interface PrivacyRequestRedactionPatternsResponse {
  patterns: string[] | null;
}

export const privacyRequestRedactionPatternsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPrivacyRequestRedactionPatterns: build.query<PrivacyRequestRedactionPatternsResponse, void>({
      query: () => ({
        url: "privacy-request/redaction-patterns",
        method: "GET",
      }),
      providesTags: ["Privacy Request Redaction Patterns"],
    }),
    updatePrivacyRequestRedactionPatterns: build.mutation<
      PrivacyRequestRedactionPatternsResponse,
      PrivacyRequestRedactionPatternsRequest
    >({
      query: (body) => ({
        url: "privacy-request/redaction-patterns",
        method: "PUT",
        body,
      }),
      invalidatesTags: ["Privacy Request Redaction Patterns"],
    }),
  }),
});

export const {
  useGetPrivacyRequestRedactionPatternsQuery,
  useUpdatePrivacyRequestRedactionPatternsMutation,
} = privacyRequestRedactionPatternsApi;
