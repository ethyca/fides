import { createSlice, PayloadAction } from "@reduxjs/toolkit";

import { CONNECTOR_TEMPLATE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";

import { ConnectorTemplateState } from "./types";

const initialState: ConnectorTemplateState = {
  loading: false,
  error: null,
};

export const connectorTemplateSlice = createSlice({
  name: "connectorTemplate",
  initialState,
  reducers: {
    setLoading: (draftState, action: PayloadAction<boolean>) => {
      draftState.loading = action.payload;
    },
    setError: (draftState, action: PayloadAction<string | null>) => {
      draftState.error = action.payload;
    },
  },
});

export const { setLoading, setError } = connectorTemplateSlice.actions;
export const { reducer } = connectorTemplateSlice;

export const connectorTemplateApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    registerConnectorTemplate: build.mutation<void, File>({
      query: (file) => {
        const formData = new FormData();
        formData.append("file", file);

        return {
          url: `${CONNECTOR_TEMPLATE}/register`,
          method: "POST",
          body: formData,
        };
      },
    }),
  }),
});

export const { useRegisterConnectorTemplateMutation } = connectorTemplateApi;
