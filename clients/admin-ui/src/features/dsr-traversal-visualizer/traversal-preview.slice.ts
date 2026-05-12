import { defaultSerializeQueryArgs } from "@reduxjs/toolkit/query";

import { baseApi } from "~/features/common/api.slice";

import { ActionType, TraversalPreviewResponse } from "./types";

export interface GetPreviewArgs {
  propertyId: string;
  actionType: ActionType;
  refresh?: boolean;
  includeUnreachable?: boolean;
}

export const traversalPreviewApi = baseApi
  .enhanceEndpoints({ addTagTypes: ["TraversalPreview"] })
  .injectEndpoints({
    endpoints: (build) => ({
      getTraversalPreview: build.query<
        TraversalPreviewResponse,
        GetPreviewArgs
      >({
        query: ({
          propertyId,
          actionType,
          refresh = false,
          includeUnreachable = true,
        }) => ({
          url: `/plus/properties/${encodeURIComponent(propertyId)}/traversal-preview`,
          params: {
            action_type: actionType,
            include_unreachable: includeUnreachable,
            refresh,
          },
        }),
        // Exclude `refresh` from the cache key so a regenerate call writes
        // back into the same entry instead of creating a parallel one. The
        // `forceRefetch` below triggers the network round-trip when the
        // caller opts in to a fresh build.
        serializeQueryArgs: ({
          queryArgs,
          endpointDefinition,
          endpointName,
        }) => {
          const argsForKey = { ...queryArgs };
          delete argsForKey.refresh;
          return defaultSerializeQueryArgs({
            queryArgs: argsForKey,
            endpointDefinition,
            endpointName,
          });
        },
        forceRefetch: ({ currentArg }) => Boolean(currentArg?.refresh),
        providesTags: (_result, _error, { propertyId, actionType }) => [
          { type: "TraversalPreview", id: `${propertyId}:${actionType}` },
        ],
      }),
    }),
  });

export const { useGetTraversalPreviewQuery, useLazyGetTraversalPreviewQuery } =
  traversalPreviewApi;
