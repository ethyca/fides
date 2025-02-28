import { Box, useDisclosure } from "fidesui";
import { ExecutionLog, PrivacyRequestEntity } from "privacy-requests/types";
import React, { useEffect, useState } from "react";

import LogDrawer from "./LogDrawer";
import TimelineEntry from "./TimelineEntry";

type ActivityTimelineProps = {
  subjectRequest: PrivacyRequestEntity;
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
      {results &&
        resultKeys.map((key, index) => (
          <TimelineEntry
            key={key}
            entryKey={key}
            logs={results[key]}
            isLast={index === resultKeys.length - 1}
            onViewLog={() => showLogs(key, results[key])}
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
