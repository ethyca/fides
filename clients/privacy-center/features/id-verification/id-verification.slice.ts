import { baseApi } from "~/features/common/api.slice";
import { IdentityVerificationConfigResponse } from "~/types/api";

export const idVerificationApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getIdVerificationConfig: build.query<
      IdentityVerificationConfigResponse,
      void
    >({
      query: () => "id-verification/config",
    }),
  }),
});

export const { useGetIdVerificationConfigQuery } = idVerificationApi;
