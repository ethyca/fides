import { baseApi } from "~/features/common/api.slice";
import { buildArrayQueryParams } from "~/features/common/utils";
import { ConsentStatus, Page_Asset_ } from "~/types/api";
import type { SortQueryParams } from "~/types/query-params";

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

export interface AssetReportingQueryParams
  extends AssetReportingFilters, SortQueryParams {
  page: number;
  size: number;
}

/**
 * Build a URL query string for asset reporting requests.
 * Uses buildArrayQueryParams to produce repeated params for arrays
 * (e.g. ?asset_type=Cookie&asset_type=Image) as required by FastAPI.
 */
const buildUrlQuery = (
  params: AssetReportingFilters & Partial<SortQueryParams>,
): string => {
  const urlParams = buildArrayQueryParams({
    asset_type: params.asset_type,
    consent_status: params.consent_status,
    system_id: params.system_id,
    data_uses: params.data_uses,
    locations: params.locations,
    sort_by: params.sort_by ? [params.sort_by].flat() : undefined,
  });

  if (params.search) {
    urlParams.append("search", params.search);
  }
  if (params.sort_asc !== undefined) {
    urlParams.append("sort_asc", String(params.sort_asc));
  }

  const qs = urlParams.toString();
  return qs ? `?${qs}` : "";
};

export const assetReportingApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllAssets: build.query<Page_Asset_, AssetReportingQueryParams>({
      query: (params) => ({
        url: `plus/asset-reporting${buildUrlQuery(params)}`,
        params: { page: params.page, size: params.size },
      }),
      providesTags: ["Asset Reporting"],
    }),

    downloadAssetReport: build.query<string, AssetReportingFilters>({
      query: (filters) => ({
        url: `plus/asset-reporting/export${buildUrlQuery(filters)}`,
        responseHandler: "text",
      }),
    }),

    getAssetReportingFilterOptions: build.query<
      AssetReportingFilterOptions,
      AssetReportingFilters
    >({
      query: (filters) => ({
        url: `plus/asset-reporting/filters${buildUrlQuery(filters)}`,
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
