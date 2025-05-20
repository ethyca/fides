import { AntList as List, Box, useDisclosure } from "fidesui";
import {
  ActivityTimelineItem,
  ExecutionLog,
  ExecutionLogStatus,
  PrivacyRequestEntity,
  PrivacyRequestResults,
} from "privacy-requests/types";
import React, { useEffect, useState } from "react";

import { formatDate } from "~/features/common/utils";

import ActivityTimelineEntry from "./ActivityTimelineEntry";
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

  const { results } = subjectRequest;

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
        tag: "Request update",
        showViewLog: hasUnresolvedError || hasSkippedEntry,
        onClick: () => showLogs(key, logs),
        isError: hasUnresolvedError,
        isSkipped: hasSkippedEntry,
      };
    });
  };

  const timelineItems = mapResultsToTimelineItems(results);

  return (
    <Box width="100%">
      <List
        className="!border-none"
        bordered={false}
        split={false}
        data-testid="activity-timeline-list"
      >
        {timelineItems.map((item) => (
          <ActivityTimelineEntry
            key={`timeline-entry-${item.title}`}
            item={item}
          />
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
