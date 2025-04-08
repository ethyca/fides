import { baseApi } from "~/features/common/api.slice";
import { getQueryParamsFromArray } from "~/features/common/utils";
import { Asset, AssetUpdate, Page_Asset_ } from "~/types/api";
import { PaginationQueryParams } from "~/types/common/PaginationQueryParams";

interface AddSystemAssetRequest {
  systemKey: string;
  asset: Asset;
}

interface UpdateSystemAssetRequest {
  systemKey: string;
  assets: AssetUpdate[];
}

interface DeleteSystemAssetRequest {
  systemKey: string;
  asset_ids: string[];
}

const systemAssetsApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getSystemAssets: build.query<
      Page_Asset_,
      PaginationQueryParams & { search: string; fides_key: string }
    >({
      query: ({ fides_key, ...params }) => ({
        method: "GET",
        url: `/plus/system-assets/${fides_key}`,
        params,
      }),
      providesTags: ["System Assets"],
    }),
    addSystemAsset: build.mutation<any, AddSystemAssetRequest>({
      query: ({ systemKey, asset }) => ({
        method: "POST",
        url: `/plus/system-assets/${systemKey}/assets`,
        body: asset,
      }),
      invalidatesTags: ["System Assets"],
    }),
    updateSystemAssets: build.mutation<any, UpdateSystemAssetRequest>({
      query: ({ systemKey, assets }) => ({
        method: "PUT",
        url: `/plus/system-assets/${systemKey}/assets/`,
        body: assets,
      }),
      invalidatesTags: ["System Assets"],
    }),
    deleteSystemAssets: build.mutation<any, DeleteSystemAssetRequest>({
      query: ({ systemKey, asset_ids }) => ({
        method: "DELETE",
        url: `/plus/system-assets/${systemKey}/assets?${getQueryParamsFromArray(
          asset_ids,
          "asset_ids",
        )}`,
      }),
      invalidatesTags: ["System Assets"],
    }),
  }),
});

export const {
  useGetSystemAssetsQuery,
  useAddSystemAssetMutation,
  useUpdateSystemAssetsMutation,
  useDeleteSystemAssetsMutation,
} = systemAssetsApi;
