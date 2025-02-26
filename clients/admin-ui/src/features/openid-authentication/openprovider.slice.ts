import { baseApi } from "~/features/common/api.slice";
import { OpenIDProvider } from "~/types/api";

interface OpenIDProviderDeleteResponse {
  message: string;
  resource: OpenIDProvider;
}

const openIDProviderApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getAllOpenIDProvidersSimple: build.query<OpenIDProvider[], void>({
      query: () => ({ url: `plus/openid-provider/simple` }),
      providesTags: ["OpenID Provider"],
    }),
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
      Partial<OpenIDProvider> & Pick<OpenIDProvider, "identifier">
    >({
      query: (params) => ({
        url: `plus/openid-provider/${params.identifier}`,
        method: "PATCH",
        body: params,
      }),
      invalidatesTags: ["OpenID Provider"],
    }),
  }),
});

export const {
  useGetAllOpenIDProvidersSimpleQuery,
  useGetAllOpenIDProvidersQuery,
  useCreateOpenIDProviderMutation,
  useUpdateOpenIDProviderMutation,
  useDeleteOpenIDProviderMutation,
} = openIDProviderApi;
