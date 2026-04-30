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
      getTraversalPreview: build.query<TraversalPreviewResponse, GetPreviewArgs>(
        {
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
          providesTags: (_result, _error, { propertyId, actionType }) => [
            { type: "TraversalPreview", id: `${propertyId}:${actionType}` },
          ],
        },
      ),
    }),
  });

export const {
  useGetTraversalPreviewQuery,
  useLazyGetTraversalPreviewQuery,
} = traversalPreviewApi;
