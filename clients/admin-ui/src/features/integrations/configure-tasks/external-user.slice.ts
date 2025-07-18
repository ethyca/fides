import { baseApi } from "~/features/common/api.slice";
import { ExternalUserCreateRequest, UserCreateResponse } from "~/types/api";

export const externalUserApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    createExternalUser: build.mutation<
      UserCreateResponse,
      ExternalUserCreateRequest
    >({
      query: (userData) => ({
        url: "plus/external-user",
        method: "POST",
        body: userData,
      }),
      invalidatesTags: ["User"], // Invalidate user cache to refresh user lists
    }),
  }),
});

export const { useCreateExternalUserMutation } = externalUserApi;
