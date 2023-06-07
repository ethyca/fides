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
    
    // We need to use a different endpoint since this is using FidesPlus.
    // Keeping this generic for now with target types in case we change this to
    // /plus/generate or some equivbalent and can reuse the ValidTargets Type
    generateS3: build.mutation<GenerateResponse, GenerateRequestPayload>({
      query: (body) => ({
        url: `classify/bucket`,
        method: "PUT",
        body,
      }),
    })
  }),
});

export const { useGenerateMutation, useGenerateS3Mutation } = scannerApi;
