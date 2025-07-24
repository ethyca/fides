import { baseApi } from "~/features/common/api.slice";
import { Page_PolicyResponse_ } from "~/types/api";

// Policy API
const policyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getPolicies: build.query<Page_PolicyResponse_, void>({
      query: () => ({ url: `/dsr/policy` }),
      providesTags: () => ["Policies"],
    }),
  }),
});

export const { useGetPoliciesQuery } = policyApi;
