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
  // Fetch comments data for this privacy request
  const { data: commentsData, isLoading } = useGetCommentsQuery({
    privacy_request_id: privacyRequestId,
    size: 100, // Use a reasonable limit
  });

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
          id: `comment-${comment.id}`,
        };
      });

  return {
    commentItems,
    isLoading,
  };
};
