import { createSlice } from "@reduxjs/toolkit";

import { baseApi } from "~/features/common/api.slice";
import { Page_StagedResourceAPIResponse_ } from "~/types/api";
import { Page_CatalogSystemResponse_ } from "~/types/api/models/Page_CatalogSystemResponse_";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

const initialState = {
  page: 1,
  pageSize: 50,
};

interface CatalogSystemQueryParams extends PaginationQueryParams {
  show_hidden?: boolean;
}

interface CatalogProjectQueryParams extends PaginationQueryParams {
  monitor_config_ids?: string[];
  show_hidden?: boolean;
}

const dataCatalogApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getCatalogSystems: build.query<
      Page_CatalogSystemResponse_,
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
      CatalogProjectQueryParams
    >({
      query: ({ monitor_config_ids, ...params }) => ({
        method: "POST",
        url: `/plus/data-catalog/project`,
        body: monitor_config_ids,
        params,
      }),
      providesTags: ["Discovery Monitor Results"],
    }),
  }),
});

export const {
  useGetCatalogSystemsQuery,
  useGetCatalogProjectsQuery,
  useLazyGetCatalogProjectsQuery,
} = dataCatalogApi;

export const dataCatalogApiSlice = createSlice({
  name: "dataCatalog",
  initialState,
  reducers: {},
});
