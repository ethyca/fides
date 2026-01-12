import { baseApi } from "~/features/common/api.slice";
import { Asset, ConsentStatus, Page_Asset_ } from "~/types/api";

export interface AssetReportingFilters {
  asset_type?: string[];
  consent_status?: ConsentStatus[];
  system_id?: string[];
  data_uses?: string[];
  search?: string;
}

export interface AssetReportingQueryParams extends AssetReportingFilters {
  page: number;
  size: number;
}

const buildQueryParams = (params: AssetReportingQueryParams) => {
  const queryParams: Record<string, any> = { page: params.page, size: params.size };

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

  return queryParams;
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
      query: (filters) => {
        const params = buildQueryParams({ ...filters, page: 1, size: 1 });
        delete params.page;
        delete params.size;

        return {
          url: "plus/asset-reporting/export",
          params,
          responseHandler: "text",
        };
      },
    }),
  }),
});

export const { useGetAllAssetsQuery, useLazyDownloadAssetReportQuery } = assetReportingApi;
