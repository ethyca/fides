import {
  AntList as List,
  AntSkeleton as Skeleton,
  Box,
  useDisclosure,
} from "fidesui";
import React, { useEffect, useMemo, useState } from "react";

import {
  ExecutionLog,
  ExecutionLogStatus,
  PrivacyRequestEntity,
} from "~/features/privacy-requests/types";

import ActivityTimelineEntry from "./ActivityTimelineEntry";
import styles from "./ActivityTimelineEntry.module.scss";
import { usePrivacyRequestComments, usePrivacyRequestEventLogs } from "./hooks";
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

  // Use our custom hooks
  const { commentItems, isLoading: isCommentsLoading } =
    usePrivacyRequestComments(privacyRequestId);
  const { eventItems, isLoading: isResultsLoading } =
    usePrivacyRequestEventLogs(results);

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

  // Combine and sort all timeline items
  const timelineItems = useMemo(() => {
    // Override the onClick handler for event items
    const eventItemsWithClickHandler = eventItems.map((item) => {
      if (item.type === "Request update" && item.title && results) {
        const key = item.title;
        if (results[key]) {
          return {
            ...item,
            onClick: () => showLogs(key, results[key]),
          };
        }
      }
      return item;
    });

    // Combine both arrays
    const allItems = [...eventItemsWithClickHandler, ...commentItems];

    // Sort by date (oldest first)
    return allItems.sort((a, b) => {
      return a.date.getTime() - b.date.getTime();
    });
  }, [eventItems, commentItems, results]);

  // Render skeleton items when loading
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
                  <ActivityTimelineEntry item={item} />
                </li>
              ))}
        </ul>
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
