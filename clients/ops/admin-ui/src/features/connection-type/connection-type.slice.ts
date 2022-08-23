import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/dist/query/react";
import { addCommonHeaders } from "common/CommonHeaders";
import { SystemType } from "datastore-connections/constants";

import type { RootState } from "../../app/store";
import { BASE_URL, CONNECTION_TYPE_ROUTE } from "../../constants";
import { selectToken } from "../auth";
import { ConnectionOption, ConnectionTypeParams } from "./types";

// Helpers
const mapFiltersToSearchParams = ({
  search,
  system_type,
}: Partial<ConnectionTypeParams>): string => {
  let queryString = "";
  if (search) {
    queryString += queryString ? `&search=${search}` : `search=${search}`;
  }
  if (system_type) {
    queryString += queryString
      ? `&system_type=${system_type}`
      : `system_type=${system_type}`;
  }
  return queryString ? `?${queryString}` : "";
};

const initialState: ConnectionTypeParams = {
  search: "",
  system_type: SystemType.SAAS, // TODO: Remove this default value when Database connectors are supported
};

export const connectionTypeSlice = createSlice({
  name: "connectionType",
  initialState,
  reducers: {
    setSearch: (state, action: PayloadAction<string>) => ({
      ...state,
      search: action.payload,
    }),
    setSystemType: (state, action: PayloadAction<SystemType | string>) => ({
      ...state,
      system_type: action.payload as SystemType,
    }),
  },
});

export const { setSearch, setSystemType } = connectionTypeSlice.actions;

export const { reducer } = connectionTypeSlice;

export const selectConnectionTypeFilters = (
  state: RootState
): ConnectionTypeParams => ({
  search: state.connectionType.search,
  system_type: state.connectionType.system_type,
});

export const connectionTypeApi = createApi({
  reducerPath: "connectionTypeApi",
  baseQuery: fetchBaseQuery({
    baseUrl: BASE_URL,
    prepareHeaders: (headers, { getState }) => {
      const token: string | null = selectToken(getState() as RootState);
      addCommonHeaders(headers, token);
      return headers;
    },
  }),
  tagTypes: ["ConnectionType"],
  endpoints: (build) => ({
    getAllConnectionTypes: build.query<
      ConnectionOption[],
      Partial<ConnectionTypeParams>
    >({
      query: (filters) => ({
        url: `${CONNECTION_TYPE_ROUTE}${mapFiltersToSearchParams(filters)}`,
      }),
      providesTags: () => ["ConnectionType"],
    }),
  }),
});

export const { useGetAllConnectionTypesQuery } = connectionTypeApi;
