import { baseApi } from "~/features/common/api.slice";

// Define your types
export interface DSRPackageResponse {
  download_url: string;
  expires_at?: string;
  request_id?: string;
}

/**
 * DSR Package API endpoints for getting download links
 *
 * These are public endpoints that don't require authentication.
 */
export const dsrPackageApi = baseApi.injectEndpoints({
  endpoints: (build) => ({

    // Get DSR package download link by request ID
    getDSRPackageByRequestId: build.query<
      DSRPackageResponse,
      { request_id: string }
    >({
      query: ({ request_id }) => ({
        url: "dsr-package-link",
        params: { request_id },
      }),
      providesTags: (result, error, arg) => [
        { type: "DSRPackage", id: arg.request_id }
      ],
    }),

    // Get DSR package download link by email
    getDSRPackageByEmail: build.query<
      DSRPackageResponse,
      { email: string }
    >({
      query: ({ email }) => ({
        url: "dsr-package-link",
        params: { email },
      }),
      providesTags: (result, error, arg) => [
        { type: "DSRPackage", id: `email:${arg.email}` }
      ],
    }),

  }),
});

// Export hooks for use in components
export const {
  useGetDSRPackageByRequestIdQuery,
  useGetDSRPackageByEmailQuery,
} = dsrPackageApi;
