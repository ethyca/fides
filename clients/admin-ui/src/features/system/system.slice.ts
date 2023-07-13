import { createSelector, createSlice, PayloadAction } from "@reduxjs/toolkit";

import type { RootState } from "~/app/store";
import { baseApi } from "~/features/common/api.slice";
import {
  BulkPutConnectionConfiguration,
  ConnectionConfigurationResponse,
  System,
  SystemResponse,
  TestStatusMessage
} from "~/types/api";

interface SystemDeleteResponse {
  message: string;
  resource: System;
}

interface UpsertResponse {
  message: string;
  inserted: number;
  updated: number;
}

export type ConnectionConfigSecretsRequest = {
  systemFidesKey: string;
  secrets: {
    [key: string]: any;
  };
};


const systemApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllSystems: build.query<SystemResponse[], void>({
      query: () => ({ url: `system/` }),
      providesTags: () => ["System"],
    }),
    getSystemByFidesKey: build.query<SystemResponse, string>({
      query: (fides_key) => ({ url: `system/${fides_key}/` }),
      providesTags: ["System"],
    }),
    // we accept 'unknown' as well since the user can paste anything in, and we rely
    // on the backend to do the validation for us
    createSystem: build.mutation<System, System | unknown>({
      query: (body) => ({
        url: `system/`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => ["Datamap", "System", "Datastore Connection"],
    }),
    deleteSystem: build.mutation<SystemDeleteResponse, string>({
      query: (key) => ({
        url: `system/${key}`,
        params: { resource_type: "system" },
        method: "DELETE",
      }),
      invalidatesTags: ["System", "Datastore Connection", "Privacy Notices"],
    }),
    upsertSystems: build.mutation<UpsertResponse, System[]>({
      query: (systems) => ({
        url: `/system/upsert`,
        method: "POST",
        body: systems,
      }),
      invalidatesTags: ["Datamap", "System", "Datastore Connection"],
    }),
    updateSystem: build.mutation<
      SystemResponse,
      Partial<System> & Pick<System, "fides_key">
    >({
      query: ({ ...patch }) => ({
        url: `system/`,
        params: { resource_type: "system" },
        method: "PUT",
        body: patch,
      }),
      invalidatesTags: [
        "Datamap",
        "System",
        "Privacy Notices",
        "Datastore Connection",
      ],
    }),
    patchSystemConnectionConfigs: build.mutation<
      BulkPutConnectionConfiguration,
      {
        systemFidesKey: string;
        connectionConfigs: Omit<
          ConnectionConfigurationResponse,
          "created_at"
        >[];
      }
    >({
      query: ({ systemFidesKey, connectionConfigs }) => ({
        url: `/system/${systemFidesKey}/connection`,
        method: "PATCH",
        body: connectionConfigs,
      }),
      invalidatesTags: ["Datamap", "System", "Datastore Connection"],
    }),
    patchSystemConnectionSecrets: build.mutation<
      TestStatusMessage,
      ConnectionConfigSecretsRequest
    >({
      query: ({secrets, systemFidesKey}) => ({
        url: `/system/${systemFidesKey}/connection/secrets?verify=false`,
        method: "PATCH",
        body: secrets,
      }),
      invalidatesTags: () => ["Datastore Connection"],
    }),
    getSystemConnectionConfigs: build.query<
      ConnectionConfigurationResponse[],
      string
    >({
      query: (systemFidesKey) => ({
        url: `/system/${systemFidesKey}/connection`,
      }),
      providesTags: ["Datamap", "System", "Datastore Connection"],
    }),
  }),
});

export const {
  useGetAllSystemsQuery,
  useGetSystemByFidesKeyQuery,
  useCreateSystemMutation,
  useUpdateSystemMutation,
  useDeleteSystemMutation,
  useUpsertSystemsMutation,
  usePatchSystemConnectionConfigsMutation,
  useGetSystemConnectionConfigsQuery,
  usePatchSystemConnectionSecretsMutation,
} = systemApi;

export interface State {
  activeSystem?: System;
  activeClassifySystemFidesKey?: string;
  systemsToClassify?: System[];
}
const initialState: State = {};

export const systemSlice = createSlice({
  name: "system",
  initialState,
  reducers: {
    setActiveSystem: (
      draftState,
      action: PayloadAction<System | undefined>
    ) => {
      draftState.activeSystem = action.payload;
    },
    setActiveClassifySystemFidesKey: (
      draftState,
      action: PayloadAction<string | undefined>
    ) => {
      draftState.activeClassifySystemFidesKey = action.payload;
    },
    setSystemsToClassify: (
      draftState,
      action: PayloadAction<System[] | undefined>
    ) => {
      draftState.systemsToClassify = action.payload;
    },
  },
});

export const {
  setActiveSystem,
  setActiveClassifySystemFidesKey,
  setSystemsToClassify,
} = systemSlice.actions;

export const { reducer } = systemSlice;

const selectSystem = (state: RootState) => state.system;

export const selectActiveSystem = createSelector(
  selectSystem,
  (state) => state.activeSystem
);

export const selectActiveClassifySystemFidesKey = createSelector(
  selectSystem,
  (state) => state.activeClassifySystemFidesKey
);

const emptySelectAllSystems: System[] = [];
export const selectAllSystems = createSelector(
  [(RootState) => RootState, systemApi.endpoints.getAllSystems.select()],
  (RootState, { data }) => data || emptySelectAllSystems
);

export const selectActiveClassifySystem = createSelector(
  [selectAllSystems, selectActiveClassifySystemFidesKey],
  (allSystems, fidesKey) => {
    if (fidesKey === undefined) {
      return undefined;
    }

    const system = allSystems?.find((s) => s.fides_key === fidesKey);
    return system;
  }
);

export const selectSystemsToClassify = createSelector(
  selectSystem,
  (state) => state.systemsToClassify
);
