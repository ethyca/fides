import { Box, Text, useDisclosure } from "fidesui";
import { ExecutionLog, PrivacyRequestEntity } from "privacy-requests/types";
import React, { useEffect, useState } from "react";

import { ExecutionLogStatus } from "~/types/api";

import LogDrawer from "./LogDrawer";
import TimelineEntry from "./TimelineEntry";

type ActivityTimelineProps = {
  subjectRequest: PrivacyRequestEntity;
};

const hasUnresolvedError = (entries: ExecutionLog[]) => {
  const groupedByCollection: {
    [key: string]: ExecutionLog;
  } = {};

  // Group the entries by collection_name and keep only the latest entry for each collection.
  entries.forEach((entry) => {
    const { collection_name: collectionName, updated_at: updatedAt } = entry;
    if (
      !groupedByCollection[collectionName] ||
      new Date(groupedByCollection[collectionName].updated_at) <
        new Date(updatedAt)
    ) {
      groupedByCollection[collectionName] = entry;
    }
  });

  // Check if any of the latest entries for the collections have an error status.
  return Object.values(groupedByCollection).some((entry) => {
    // For entries with a collection_name, check for later complete status
    if (entry.collection_name) {
      const latestComplete = entries.find(
        (e) =>
          e.status.toLowerCase() === "complete" &&
          !e.collection_name && // completion entries have null collection_name
          new Date(e.updated_at) > new Date(entry.updated_at),
      );

      return !latestComplete && entry.status === ExecutionLogStatus.ERROR;
    }

    return entry.status === ExecutionLogStatus.ERROR;
  });
};

const ActivityTimeline = ({ subjectRequest }: ActivityTimelineProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const [currentLogs, setCurrentLogs] = useState<ExecutionLog[]>([]);
  const [currentKey, setCurrentKey] = useState<string>("");
  const [isViewingError, setViewingError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const { results } = subjectRequest;
  const resultKeys = results ? Object.keys(results) : [];

  // Update currentLogs when results change and we have a selected key
  useEffect(() => {
    if (currentKey && results && results[currentKey]) {
      setCurrentLogs(results[currentKey]);
    }
  }, [results, currentKey]);

  const openErrorPanel = (message: string) => {
    setErrorMessage(message);
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

  return (
    <Box width="100%">
      <Text color="gray.900" fontSize="md" fontWeight="500" mb={1}>
        Activity timeline
      </Text>
      {resultKeys.map((key, index) => (
        <TimelineEntry
          key={key}
          entryKey={key}
          hasError={hasUnresolvedError(results![key])}
          isLast={index === resultKeys.length - 1}
          onViewLog={() => showLogs(key, results![key])}
        />
      ))}
      <LogDrawer
        isOpen={isOpen}
        onClose={closeDrawer}
        currentLogs={currentLogs}
        isViewingError={isViewingError}
        errorMessage={errorMessage}
        onOpenErrorPanel={openErrorPanel}
        onCloseErrorPanel={closeErrorPanel}
      />
    </Box>
  );
};

export default ActivityTimeline;
