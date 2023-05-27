import { createSlice } from "@reduxjs/toolkit";

import { CONNECTOR_TEMPLATE } from "~/constants";
import { baseApi } from "~/features/common/api.slice";

export interface State {}
const initialState: State = {};

export const connectorTemplateSlice = createSlice({
  name: "connectorTemplate",
  initialState,
  reducers: {},
});

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
