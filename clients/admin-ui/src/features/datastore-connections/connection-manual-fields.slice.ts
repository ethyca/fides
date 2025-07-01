import { baseApi } from "~/features/common/api.slice";
import {
  ManualFieldCreate,
  ManualFieldRequestType,
  ManualFieldResponse,
  ManualFieldUpdate,
} from "~/types/api";

import { PLUS_CONNECTION_API_ROUTE } from "../../constants";

export const connectionManualFieldsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getManualFields: build.query<
      ManualFieldResponse[],
      { connectionKey: string; requestType?: ManualFieldRequestType }
    >({
      query: ({ connectionKey, requestType }) => {
        const baseUrl = `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-fields`;
        const queryString = requestType ? `?request_type=${requestType}` : "";
        return {
          url: baseUrl + queryString,
          method: "GET",
        };
      },
      providesTags: () => ["Manual Fields"],
    }),
    getManualField: build.query<
      ManualFieldResponse,
      { connectionKey: string; manualFieldId: string }
    >({
      query: ({ connectionKey, manualFieldId }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-field/${manualFieldId}`,
        method: "GET",
      }),
      providesTags: (result) => [{ type: "Manual Fields", id: result?.id }],
    }),
    createManualField: build.mutation<
      ManualFieldResponse,
      { connectionKey: string; body: ManualFieldCreate }
    >({
      query: ({ connectionKey, body }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-field`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["Manual Fields"],
    }),
    updateManualField: build.mutation<
      ManualFieldResponse,
      { connectionKey: string; manualFieldId: string; body: ManualFieldUpdate }
    >({
      query: ({ connectionKey, manualFieldId, body }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-field/${manualFieldId}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: () => ["Manual Fields"],
    }),
    deleteManualField: build.mutation<
      void,
      { connectionKey: string; manualFieldId: string }
    >({
      query: ({ connectionKey, manualFieldId }) => ({
        url: `${PLUS_CONNECTION_API_ROUTE}/${connectionKey}/manual-field/${manualFieldId}`,
        method: "DELETE",
      }),
      invalidatesTags: () => ["Manual Fields"],
    }),
  }),
});

export const {
  useGetManualFieldsQuery,
  useGetManualFieldQuery,
  useCreateManualFieldMutation,
  useUpdateManualFieldMutation,
  useDeleteManualFieldMutation,
} = connectionManualFieldsApi;
