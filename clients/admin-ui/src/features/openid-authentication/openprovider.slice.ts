import { baseApi } from "~/features/common/api.slice";
import { OpenIDProvider, SystemResponse } from "~/types/api";

interface OpenIDProviderDeleteResponse {
  message: string;
  resource: OpenIDProvider;
}

const openIDProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllOpenIDProviders: build.query<SystemResponse[], void>({
      query: () => ({ url: `plus/openid-provider` }),
      providesTags: ["OpenID Provider"],
    }),
    createOpenIDProvider: build.mutation<
      SystemResponse,
      OpenIDProvider | unknown
    >({
      query: (body) => ({
        url: `plus/openid-provider`,
        method: "POST",
        body,
      }),
      invalidatesTags: ["OpenID Provider"],
    }),
    deleteOpenIDProvider: build.mutation<OpenIDProviderDeleteResponse, string>({
      query: (key) => ({
        url: `plus/openid-provider/${key}`,
        method: "DELETE",
      }),
      invalidatesTags: ["OpenID Provider"],
    }),
    updateOpenIDProvider: build.mutation<
      SystemResponse,
      Partial<OpenIDProvider> & Pick<OpenIDProvider, "fides_key">
    >({
      query: (params) => ({
        url: `plus/openid-provider/${params.id}`,
        method: "PATCH",
        body: params,
      }),
      invalidatesTags: ["OpenID Provider"],
    }),
  }),
});

export const {
  useGetAllOpenIDProvidersQuery,
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
  useDeleteOpenIDProviderMutation,
} = openIDProviderApi;
