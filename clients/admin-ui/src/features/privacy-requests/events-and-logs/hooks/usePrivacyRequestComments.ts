import { AntMessage as message } from "fidesui";
import { useEffect } from "react";

import { useFeatures } from "~/features/common/features";
import { useGetCommentsQuery } from "~/features/privacy-requests/comments/privacy-request-comments.slice";
import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
} from "~/features/privacy-requests/types";
import { CommentResponse } from "~/types/api/models/CommentResponse";

/**
 * Hook for fetching and processing privacy request comments
 */
export const usePrivacyRequestComments = (privacyRequestId: string) => {
  const { plus: isPlusEnabled } = useFeatures();

  // Fetch comments data for this privacy request
  const {
    data: commentsData,
    isLoading,
    error,
  } = useGetCommentsQuery(
    {
      privacy_request_id: privacyRequestId,
      size: 100, // Use a reasonable limit
    },
    {
      skip: !isPlusEnabled,
    },
  );

  // Handle error state
  useEffect(() => {
    if (error) {
      message.error("Failed to fetch the request comments");
    }
  }, [error]);

  // Map comments to ActivityTimelineItem
  const commentItems: ActivityTimelineItem[] = !commentsData?.items
    ? []
    : commentsData.items.map((comment: CommentResponse) => {
        const author =
          comment.user_first_name && comment.user_last_name
            ? `${comment.user_first_name} ${comment.user_last_name}`
            : comment.username || "Unknown";

        return {
          author,
          date: new Date(comment.created_at),
          type: ActivityTimelineItemTypeEnum.INTERNAL_COMMENT,
          showViewLog: false,
          description: comment.comment_text,
          isError: false,
          isSkipped: false,
          isAwaitingInput: false,
          id: `comment-${comment.id}`,
        };
      });

  return {
    commentItems,
    isLoading,
  };
};
