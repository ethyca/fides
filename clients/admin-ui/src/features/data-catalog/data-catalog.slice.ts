import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import {
  Page_StagedResourceAPIResponse_,
  Page_SystemWithMonitorKeys_,
} from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

const initialState = {
  page: 1,
  pageSize: 50,
};

interface CatalogSystemQueryParams extends PaginationQueryParams {
  show_hidden?: boolean;
}

interface CatalogResourceQueryParams extends PaginationQueryParams {
  monitor_config_ids?: string[];
  show_hidden?: boolean;
}

const dataCatalogApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getCatalogSystems: build.query<
      Page_SystemWithMonitorKeys_,
      CatalogSystemQueryParams
    >({
      query: (params) => ({
        method: "GET",
        url: `/plus/data-catalog/system`,
        params,
      }),
      providesTags: ["Catalog Systems"],
    }),
    getCatalogProjects: build.query<
      Page_StagedResourceAPIResponse_,
      CatalogResourceQueryParams
    >({
      query: ({ ...params }) => ({
        method: "GET",
        url: `/plus/data-catalog/project`,
        params,
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
    getCatalogDatasets: build.query<
      Page_StagedResourceAPIResponse_,
      CatalogResourceQueryParams
    >({
      query: ({ ...params }) => ({
        method: "GET",
        url: `/plus/data-catalog/dataset`,
        params,
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
  }),
});

export const {
  useGetCatalogSystemsQuery,
  useGetCatalogProjectsQuery,
  useGetCatalogDatasetsQuery,
} = dataCatalogApi;

export const dataCatalogApiSlice = createSlice({
  name: "dataCatalog",
  initialState,
  reducers: {},
});
