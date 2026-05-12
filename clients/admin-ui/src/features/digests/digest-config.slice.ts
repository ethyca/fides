import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  DigestConfigRequest,
  DigestConfigResponse,
  DigestType,
  Page_DigestConfigResponse_,
} from "~/types/api";

export interface State {}

const initialState: State = {};

// Query parameter interfaces
interface ListDigestConfigsParams {
  digest_config_type: DigestType;
  enabled?: boolean | null;
  page?: number;
  size?: number;
}

interface GetDigestConfigParams {
  config_id: string;
}

interface CreateDigestConfigParams {
  digest_config_type: DigestType;
  data: DigestConfigRequest;
}

interface UpdateDigestConfigParams {
  config_id: string;
  digest_config_type: DigestType;
  data: DigestConfigRequest;
}

interface DeleteDigestConfigParams {
  config_id: string;
  digest_config_type: DigestType;
}

interface TestDigestConfigParams {
  digest_config_id: string;
  digest_config_type: DigestType;
  test_email: string;
}

const digestConfigApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    // List digest configs
    listDigestConfigs: build.query<
      Page_DigestConfigResponse_,
      ListDigestConfigsParams
    >({
      query: ({ digest_config_type, enabled, page = 1, size = 50 }) => ({
        url: "plus/digest-config",
        method: "GET",
        params: {
          digest_config_type,
          enabled,
          page,
          size,
        },
      }),
      providesTags: ["Digest Configs"],
    }),

    // Get single digest config by ID
    getDigestConfigById: build.query<
      DigestConfigResponse,
      GetDigestConfigParams
    >({
      query: ({ config_id }) => ({
        url: `plus/digest-config/${config_id}`,
        method: "GET",
      }),
      providesTags: ["Digest Configs"],
    }),

    // Create digest config
    createDigestConfig: build.mutation<
      DigestConfigResponse,
      CreateDigestConfigParams
    >({
      query: ({ digest_config_type, data }) => ({
        url: "plus/digest-config",
        method: "POST",
        params: { digest_config_type },
        body: data,
      }),
      invalidatesTags: ["Digest Configs"],
    }),

    // Update digest config
    updateDigestConfig: build.mutation<
      { message: string },
      UpdateDigestConfigParams
    >({
      query: ({ config_id, digest_config_type, data }) => ({
        url: `plus/digest-config/${config_id}`,
        method: "PUT",
        params: { digest_config_type },
        body: data,
      }),
      invalidatesTags: ["Digest Configs"],
    }),

    // Delete digest config
    deleteDigestConfig: build.mutation<void, DeleteDigestConfigParams>({
      query: ({ config_id, digest_config_type }) => ({
        url: `plus/digest-config/${config_id}`,
        method: "DELETE",
        params: { digest_config_type },
      }),
      invalidatesTags: ["Digest Configs"],
    }),

    // Test digest config
    testDigestConfig: build.mutation<
      Record<string, unknown>,
      TestDigestConfigParams
    >({
      query: ({ digest_config_id, digest_config_type, test_email }) => ({
        url: "plus/digest-config/test",
        method: "POST",
        params: { digest_config_id, digest_config_type, test_email },
      }),
    }),
  }),
});

export const {
  useListDigestConfigsQuery,
  useLazyListDigestConfigsQuery,
  useGetDigestConfigByIdQuery,
  useCreateDigestConfigMutation,
  useUpdateDigestConfigMutation,
  useDeleteDigestConfigMutation,
  useTestDigestConfigMutation,
} = digestConfigApi;

export const digestConfigSlice = createSlice({
  name: "digestConfig",
  initialState,
  reducers: {},
});

export const { reducer } = digestConfigSlice;
