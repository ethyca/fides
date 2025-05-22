import {
  AntList as List,
  AntSkeleton as Skeleton,
  Box,
  useDisclosure,
} from "fidesui";
import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  ExecutionLog,
  ExecutionLogStatus,
  PrivacyRequestEntity,
  PrivacyRequestResults,
} from "privacy-requests/types";
import React, { useEffect, useMemo, useState } from "react";

import { formatDate } from "~/features/common/utils";
import { useGetCommentsQuery } from "~/features/privacy-requests/comments/privacy-request-comments.slice";
import { CommentResponse } from "~/types/api/models/CommentResponse";

import ActivityTimelineEntry from "./ActivityTimelineEntry";
import styles from "./ActivityTimelineEntry.module.scss";
import LogDrawer from "./LogDrawer";

type ActivityTimelineProps = {
  subjectRequest: PrivacyRequestEntity;
};

const ActivityTimeline = ({ subjectRequest }: ActivityTimelineProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [currentLogs, setCurrentLogs] = useState<ExecutionLog[]>([]);
  const [currentKey, setCurrentKey] = useState<string>("");
  const [isViewingError, setViewingError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [currentStatus, setCurrentStatus] = useState<ExecutionLogStatus>(
    ExecutionLogStatus.ERROR,
  );

  const { results, id: privacyRequestId } = subjectRequest;

  // Fetch comments data for this privacy request
  const { data: commentsData, isLoading: isCommentsLoading } =
    useGetCommentsQuery({
      privacy_request_id: privacyRequestId,
      size: 100, // Use a reasonable limit
    });

  // Determine if results are loading
  const isResultsLoading = !results;

  // Combined loading state
  const isLoading = isCommentsLoading || isResultsLoading;

  // Update currentLogs when results change and we have a selected key
  useEffect(() => {
    if (currentKey && results && results[currentKey]) {
      setCurrentLogs(results[currentKey]);
    }
  }, [results, currentKey]);

  const openErrorPanel = (message: string, status?: ExecutionLogStatus) => {
    setErrorMessage(message);
    if (status) {
      setCurrentStatus(status);
    }
    setViewingError(true);
  };

  const closeErrorPanel = () => {
    setViewingError(false);
  };

  const closeDrawer = () => {
    if (isViewingError) {
      closeErrorPanel();
    }
    setCurrentKey("");
    onClose();
  };

  const showLogs = (key: string, logs: ExecutionLog[]) => {
    setCurrentKey(key);
    setCurrentLogs(logs);
    onOpen();
  };

  // Map from source events to ActivityTimelineItems
  const mapResultsToTimelineItems = (
    resultsData?: PrivacyRequestResults,
  ): ActivityTimelineItem[] => {
    if (!resultsData) {
      return [];
    }

    return Object.entries(resultsData).map(([key, logs]) => {
      const hasUnresolvedError = logs.some(
        (log) => log.status === ExecutionLogStatus.ERROR,
      );
      const hasSkippedEntry = logs.some(
        (log) => log.status === ExecutionLogStatus.SKIPPED,
      );

      return {
        author: "Fides",
        title: key,
        date: formatDate(logs[0].updated_at),
        type: ActivityTimelineItemTypeEnum.REQUEST_UPDATE,
        showViewLog: hasUnresolvedError || hasSkippedEntry,
        onClick: () => showLogs(key, logs),
        isError: hasUnresolvedError,
        isSkipped: hasSkippedEntry,
        id: `request-${key}`,
      };
    });
  };

  // Map comments to ActivityTimelineItem
  const mapCommentsToTimelineItems = (
    comments?: CommentResponse[],
  ): ActivityTimelineItem[] => {
    if (!comments || comments.length === 0) {
      return [];
    }

    return comments.map((comment) => {
      const author =
        comment.user_first_name && comment.user_last_name
          ? `${comment.user_first_name} ${comment.user_last_name}`
          : comment.username || "Unknown";

      return {
        author,
        date: formatDate(comment.created_at),
        type: ActivityTimelineItemTypeEnum.INTERNAL_COMMENT,
        showViewLog: false,
        description: comment.comment_text,
        isError: false,
        isSkipped: false,
        id: `comment-${comment.id}`,
      };
    });
  };

  // Combine and sort all timeline items
  const timelineItems = useMemo(() => {
    const requestItems = mapResultsToTimelineItems(results);
    const commentItems = mapCommentsToTimelineItems(commentsData?.items);

    // Combine both arrays
    const allItems = [...requestItems, ...commentItems];

    // Sort by date (oldest first)
    return allItems.sort((a, b) => {
      return new Date(a.date).getTime() - new Date(b.date).getTime();
    });
  }, [results, commentsData]);

  // Render skeleton items when loading
  const renderSkeletonItems = () => {
    // Use fixed IDs instead of array indices
    const skeletonIds = [
      "timeline-skeleton-1",
      "timeline-skeleton-2",
      "timeline-skeleton-3",
    ];

    return skeletonIds.map((id) => (
      <div key={id} className={styles.itemButton} style={{ padding: "16px" }}>
        <Skeleton paragraph={{ rows: 2 }} active />
      </div>
    ));
  };

  return (
    <Box width="100%">
      <List
        className="!border-none"
        bordered={false}
        split={false}
        data-testid="activity-timeline-list"
      >
        {isLoading
          ? renderSkeletonItems()
          : timelineItems.map((item) => (
              <ActivityTimelineEntry key={item.id} item={item} />
            ))}
      </List>
      <LogDrawer
        isOpen={isOpen}
        onClose={closeDrawer}
        currentLogs={currentLogs}
        isViewingError={isViewingError}
        errorMessage={errorMessage}
        currentStatus={currentStatus}
        onOpenErrorPanel={openErrorPanel}
        onCloseErrorPanel={closeErrorPanel}
      />
    </Box>
  );
};

export default ActivityTimeline;
