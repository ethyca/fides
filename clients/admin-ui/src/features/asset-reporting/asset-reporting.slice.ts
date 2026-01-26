import { baseApi } from "~/features/common/api.slice";
import { ConsentStatus, Page_Asset_ } from "~/types/api";

export interface AssetReportingFilters {
  asset_type?: string[];
  consent_status?: ConsentStatus[];
  system_id?: string[];
  data_uses?: string[];
  locations?: string[];
  search?: string;
}

export interface AssetReportingFilterOptions {
  asset_type?: string[] | null;
  consent_status?: string[] | null;
  system_id?: string[] | null;
  data_uses?: string[] | null;
  locations?: string[] | null;
}

export interface AssetReportingQueryParams extends AssetReportingFilters {
  page: number;
  size: number;
}

const buildFilterParams = (params: AssetReportingFilters) => {
  const queryParams: Record<string, any> = {};

  if (params.search) {
    queryParams.search = params.search;
  }

  // Handle array parameters (FastAPI expects repeated params: ?asset_type=Cookie&asset_type=Image)
  if (params.asset_type?.length) {
    queryParams.asset_type = params.asset_type;
  }
  if (params.consent_status?.length) {
    queryParams.consent_status = params.consent_status;
  }
  if (params.system_id?.length) {
    queryParams.system_id = params.system_id;
  }
  if (params.data_uses?.length) {
    queryParams.data_uses = params.data_uses;
  }
  if (params.locations?.length) {
    queryParams.locations = params.locations;
  }

  return queryParams;
};

const buildQueryParams = (params: AssetReportingQueryParams) => {
  return {
    page: params.page,
    size: params.size,
    ...buildFilterParams(params),
  };
};

export const assetReportingApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllAssets: build.query<Page_Asset_, AssetReportingQueryParams>({
      query: (params) => ({
        url: "plus/asset-reporting",
        params: buildQueryParams(params),
      }),
      providesTags: ["Asset Reporting"],
    }),

    downloadAssetReport: build.query<any, AssetReportingFilters>({
      query: (filters) => ({
        url: "plus/asset-reporting/export",
        params: buildFilterParams(filters),
        responseHandler: "text",
      }),
    }),

    getAssetReportingFilterOptions: build.query<
      AssetReportingFilterOptions,
      AssetReportingFilters
    >({
      query: (filters) => ({
        url: "plus/asset-reporting/filters",
        params: buildFilterParams(filters),
      }),
      providesTags: ["Asset Reporting"],
    }),
  }),
});

export const {
  useGetAllAssetsQuery,
  useLazyDownloadAssetReportQuery,
  useGetAssetReportingFilterOptionsQuery,
} = assetReportingApi;
