import { baseApi } from "~/features/common/api.slice";
import { OpenIDProvider } from "~/types/api";

interface OpenIDProviderDeleteResponse {
  message: string;
  resource: OpenIDProvider;
}

const openIDProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllOpenIDProviders: build.query<OpenIDProvider[], void>({
      query: () => ({ url: `plus/openid-provider` }),
      providesTags: ["OpenID Provider"],
    }),
    createOpenIDProvider: build.mutation<
      OpenIDProvider,
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
      OpenIDProvider,
      Partial<OpenIDProvider> & Pick<OpenIDProvider, "id">
    >({
      query: (params) => ({
        url: `plus/openid-provider/${params.id}`,
        method: "PATCH",
        body: params,
      }),
      invalidatesTags: ["OpenID Provider"],
    }),
    testOpenIDProvider: build.mutation<
      OpenIDProvider,
      Partial<OpenIDProvider> & Pick<OpenIDProvider, "id">
    >({
      query: (params) => ({
        url: `plus/openid-provider/${params.id}/test`,
        method: "GET",
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
  useTestOpenIDProviderMutation,
} = openIDProviderApi;
