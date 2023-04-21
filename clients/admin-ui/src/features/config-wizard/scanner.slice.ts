import { baseApi } from "~/features/common/api.slice";
import { GenerateRequestPayload, GenerateResponse } from "~/types/api";

const scannerApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    generate: build.mutation<GenerateResponse, GenerateRequestPayload>({
      query: (body) => ({
        url: `generate`,
        method: "POST",
        body,
      }),
    }),
  }),
});

export const { useGenerateMutation } = scannerApi;
