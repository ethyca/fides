import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";

import type { RootState } from "../../app/store";
import { BASE_URL, CONNECTION_ROUTE } from "../../constants";
import { selectToken } from "../auth";
import {
  DatastoreConnection,
  DatastoreConnectionParams,
  DatastoreConnectionResponse,
  DatastoreConnectionStatus,
} from "./types";

function mapFiltersToSearchParams({
  search,
  page,
  size,
}: Partial<DatastoreConnectionParams>): any {
  return {
    ...(search ? { search } : {}),
    ...(page ? { page: `${page}` } : {}),
    ...(typeof size !== "undefined" ? { size: `${size}` } : {}),
  };
}
const initialState: DatastoreConnectionParams = {
  search: "",
  page: 1,
  size: 25,
};

export const datastoreConnectionSlice = createSlice({
  name: "datastoreConnections",
  initialState,
  reducers: {
    setSearch: (state, action: PayloadAction<string>) => ({
      ...state,
      page: initialState.page,
      search: action.payload,
    }),
    setPage: (state, action: PayloadAction<number>) => ({
      ...state,
      page: action.payload,
    }),
    setSize: (state, action: PayloadAction<number>) => ({
      ...state,
      page: initialState.page,
      size: action.payload,
    }),
  },
});

export const { setSearch, setSize, setPage } = datastoreConnectionSlice.actions;
export const selectDatastoreConnectionFilters = (
  state: RootState
): DatastoreConnectionParams => ({
  search: state.datastoreConnections.search,
  page: state.datastoreConnections.page,
  size: state.datastoreConnections.size,
});

export const { reducer } = datastoreConnectionSlice;

export const datastoreConnectionApi = createApi({
  reducerPath: "datastoreConnectionApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token = selectToken(getState() as RootState);
      headers.set("Access-Control-Allow-Origin", "*");
      if (token) {
        headers.set("authorization", `Bearer ${token}`);
      }
      return headers;
    },
  }),
  tagTypes: ["DatastoreConnection"],
  endpoints: (build) => ({
    getAllDatastoreConnections: build.query<
      DatastoreConnectionResponse,
      Partial<DatastoreConnectionParams>
    >({
      query: (filters) => ({
        url: CONNECTION_ROUTE,
        params: mapFiltersToSearchParams(filters),
      }),
      providesTags: () => ["DatastoreConnection"],
    }),
    getDatastoreConnectionByKey: build.query<DatastoreConnection, string>({
      query: (key) => ({
        url: `${CONNECTION_ROUTE}/${key}`,
      }),
      providesTags: (result) => [
        { type: "DatastoreConnection", id: result!.key },
      ],
      keepUnusedDataFor: 1,
    }),
    getDatastoreConnectionStatus: build.query<
      DatastoreConnectionStatus,
      string
    >({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}/test`,
      }),
      providesTags: () => ["DatastoreConnection"],
      async onQueryStarted(key, { dispatch, queryFulfilled, getState }) {
        try {
          await queryFulfilled;

          const request = dispatch(
            datastoreConnectionApi.endpoints.getDatastoreConnectionByKey.initiate(
              key
            )
          );
          const result = await request.unwrap();
          request.unsubscribe();

          const state = getState() as RootState;
          const filters = selectDatastoreConnectionFilters(state);

          dispatch(
            datastoreConnectionApi.util.updateQueryData(
              "getAllDatastoreConnections",
              filters,
              (draft) => {
                const newList = draft.items.map((d) => {
                  if (d.key === key) {
                    return { ...result };
                  }
                  return { ...d };
                });
                // eslint-disable-next-line no-param-reassign
                draft.items = newList;
              }
            )
          );
        } catch {
          throw new Error("Error while testing connection");
        }
      },
    }),
    patchDatastoreConnections: build.mutation({
      query: () => ({
        url: CONNECTION_ROUTE,
        method: "PATCH",
        body: {},
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    deleteDatastoreConnection: build.mutation({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}`,
        method: "DELETE",
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
    updateDatastoreConnectionSecrets: build.mutation({
      query: (id) => ({
        url: `${CONNECTION_ROUTE}/${id}/secret`,
        method: "PUT",
        body: {},
      }),
      invalidatesTags: () => ["DatastoreConnection"],
    }),
  }),
});

export const {
  useGetAllDatastoreConnectionsQuery,
  useLazyGetDatastoreConnectionStatusQuery,
} = datastoreConnectionApi;
