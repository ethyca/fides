import { baseApi } from "~/features/common/api.slice";

export type SystemHistory = {
  edited_by: string;
  system_key: string;
  before: object;
  after: object;
  created_at: string;
};

export type SystemHistoryResponse = {
  items: SystemHistory[];
  total: number;
  page: number;
  size: number;
};

// System History API
const systemHistoryApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSystemHistory: build.query<
      SystemHistoryResponse,
      { system_key: string }
    >({
      query: (params) => ({ url: `system/${params.system_key}/history` }),
      providesTags: () => ["System History"],
    }),
  }),
});

export const { useGetSystemHistoryQuery } = systemHistoryApi;
