import { baseApi } from "~/features/common/api.slice";
import { RedactionEntry, RedactionsRequest } from "~/types/api";

import { AccessPackageResponse } from "./types";

export const accessPackageApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAccessPackage: build.query<AccessPackageResponse, string>({
      query: (privacyRequestId) => ({
        url: `plus/privacy-request/${privacyRequestId}/access-package`,
      }),
      providesTags: (_result, _error, privacyRequestId) => [
        { type: "Access Package", id: privacyRequestId },
      ],
    }),

    updateAccessPackageRedactions: build.mutation<
      { redactions: RedactionEntry[] },
      { privacy_request_id: string; redactions: RedactionEntry[] }
    >({
      query: ({ privacy_request_id: privacyRequestId, redactions }) => {
        const body: RedactionsRequest = { redactions };
        return {
          url: `plus/privacy-request/${privacyRequestId}/access-package/redactions`,
          method: "PUT",
          body,
        };
      },
      invalidatesTags: (_result, _error, { privacy_request_id: id }) => [
        { type: "Access Package", id },
      ],
    }),

    approveAccessPackage: build.mutation<void, string>({
      query: (privacyRequestId) => ({
        url: `plus/privacy-request/${privacyRequestId}/access-package/approve`,
        method: "POST",
      }),
      invalidatesTags: (_result, _error, privacyRequestId) => [
        { type: "Access Package", id: privacyRequestId },
        { type: "Request" },
      ],
    }),

    downloadAccessPackage: build.query<Blob, string>({
      query: (privacyRequestId) => ({
        url: `plus/privacy-request/${privacyRequestId}/access-package/download`,
        responseHandler: (response) => response.blob(),
        cache: "no-cache",
      }),
    }),
  }),
});

export const {
  useGetAccessPackageQuery,
  useUpdateAccessPackageRedactionsMutation,
  useApproveAccessPackageMutation,
  useLazyDownloadAccessPackageQuery,
} = accessPackageApi;
