import {
  AntList as List,
  AntSkeleton as Skeleton,
  Box,
  useDisclosure,
} from "fidesui";
import React, { useCallback, useEffect, useMemo, useState } from "react";

import {
  ActivityTimelineItem,
  ActivityTimelineItemTypeEnum,
  ExecutionLog,
  ExecutionLogStatus,
  PrivacyRequestResults,
} from "~/features/privacy-requests/types";
import { PrivacyRequestVerboseResponse } from "~/types/api";

import ActivityTimelineEntry from "./ActivityTimelineEntry";
import styles from "./ActivityTimelineEntry.module.scss";
import {
  usePrivacyRequestComments,
  usePrivacyRequestEventLogs,
  usePrivacyRequestManualTasks,
} from "./hooks";
import LogDrawer from "./LogDrawer";

type ActivityTimelineProps = {
  subjectRequest: PrivacyRequestVerboseResponse;
};

/**
 * Look ye upon all of the type casting within and despair
 * If you fill your apis with 'any' ol' types, anything is possible and nothing is real
 */
const ActivityTimeline = ({ subjectRequest }: ActivityTimelineProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [currentLogs, setCurrentLogs] = useState<ExecutionLog[]>([]);
  const [currentKey, setCurrentKey] = useState<string>("");
  const [isViewingError, setViewingError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [currentStatus, setCurrentStatus] = useState<ExecutionLogStatus>(
    ExecutionLogStatus.ERROR,
  );

  const { results = [], id: privacyRequestId } = subjectRequest;

  const { commentItems, isLoading: isCommentsLoading } =
    usePrivacyRequestComments(privacyRequestId);

  const { eventItems, isLoading: isResultsLoading } =
    /*
     * Another "the backend made me do it"
     * Unfortunately not a regression since this is just casting to the previous type, just at a lower level
     */
    usePrivacyRequestEventLogs(results as PrivacyRequestResults);
  const {
    manualTaskItems,
    taskCommentIds,
    isLoading: isManualTasksLoading,
  } = usePrivacyRequestManualTasks(privacyRequestId);

  const isLoading =
    isCommentsLoading || isResultsLoading || isManualTasksLoading;

  useEffect(() => {
    if (
      currentKey &&
      results &&
      (results as PrivacyRequestResults)[currentKey]
    ) {
      setCurrentLogs((results as PrivacyRequestResults)[currentKey]);
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

  const showLogs = useCallback(
    (key: string, logs: ExecutionLog[]) => {
      setCurrentKey(key);
      setCurrentLogs(logs);
      onOpen();
    },
    [onOpen],
  );

  // Flatten all event logs from all groups for total calculation
  const allEventLogs = useMemo(() => {
    if (!results) {
      return [];
    }
    return Object.values(results).flat();
  }, [results]);

  // Filter out comments that are already included in manual tasks
  // to avoid showing the same comments twice in the timeline
  const filteredCommentItems = useMemo(() => {
    return commentItems.filter((commentItem) => {
      // Extract comment ID from the comment item ID (format: "comment-{id}")
      const commentId = commentItem.id.replace("comment-", "");
      return !taskCommentIds.has(commentId);
    });
  }, [commentItems, taskCommentIds]);

  const timelineItems = useMemo(() => {
    const eventItemsWithClickHandler = eventItems.map((item) => {
      if (item.type === "Request update" && item.title && results) {
        const key = item.title;
        if ((results as PrivacyRequestResults)[key]) {
          return {
            ...item,
            onClick: () =>
              showLogs(key, (results as PrivacyRequestResults)[key]),
          };
        }
      }
      return item;
    });

    // Create initial access request item
    const initialRequestItem = {
      author: "Fides",
      title: "Access request received",
      date: subjectRequest.created_at
        ? new Date(subjectRequest.created_at)
        : null,
      type: ActivityTimelineItemTypeEnum.REQUEST_UPDATE,
      showViewLog: false,
      isError: false,
      isSkipped: false,
      isAwaitingInput: false,
      id: "initial-request",
    };

    const allItems = [
      initialRequestItem,
      ...eventItemsWithClickHandler,
      ...filteredCommentItems,
      ...manualTaskItems,
    ];

    // Sort by date (oldest first)
    return allItems.sort((a, b) => {
      const dateA = a.date ? new Date(a.date).getTime() : new Date().getTime();
      const dateB = b.date ? new Date(b.date).getTime() : new Date().getTime();

      return dateA - dateB;
    });
  }, [
    eventItems,
    filteredCommentItems,
    manualTaskItems,
    results,
    showLogs,
    subjectRequest.created_at,
  ]);

  const renderSkeletonItems = () => (
    <div className={styles.itemButton} data-testid="timeline-skeleton">
      <Skeleton paragraph={{ rows: 2 }} active />
    </div>
  );

  return (
    <Box width="100%">
      <List
        className="!border-none"
        bordered={false}
        split={false}
        data-testid="activity-timeline-list"
      >
        <ul className="!list-none">
          {isLoading
            ? renderSkeletonItems()
            : timelineItems.map((item) => (
                <li key={item.id}>
                  {/**
                   * This should be double checked
                   * Looks like different types of objects could be given here
                   */}
                  <ActivityTimelineEntry item={item as ActivityTimelineItem} />
                </li>
              ))}
        </ul>
      </List>
      <LogDrawer
        isOpen={isOpen}
        onClose={closeDrawer}
        currentLogs={currentLogs}
        allEventLogs={allEventLogs as ExecutionLog[]}
        isViewingError={isViewingError}
        errorMessage={errorMessage}
        currentStatus={currentStatus}
        onOpenErrorPanel={openErrorPanel}
        onCloseErrorPanel={closeErrorPanel}
        privacyRequest={subjectRequest}
      />
    </Box>
  );
};

export default ActivityTimeline;
