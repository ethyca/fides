import { Button, Drawer, Flex, Icons } from "fidesui";
import {
  ExecutionLog,
  ExecutionLogStatus,
  PrivacyRequestEntity,
} from "privacy-requests/types";
import React from "react";

import EventDetail from "./EventDetail";
import EventLog from "./EventLog";

type LogDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  currentLogs: ExecutionLog[];
  allEventLogs?: ExecutionLog[]; // All event logs from all groups for total calculation
  isViewingError: boolean;
  errorMessage: string;
  currentStatus?: ExecutionLogStatus;
  onCloseErrorPanel: () => void;
  onOpenErrorPanel: (message: string, status?: ExecutionLogStatus) => void;
  privacyRequest?: PrivacyRequestEntity;
};

const LogDrawer = ({
  isOpen,
  onClose,
  currentLogs,
  allEventLogs,
  isViewingError,
  errorMessage,
  currentStatus = ExecutionLogStatus.ERROR,
  onCloseErrorPanel,
  onOpenErrorPanel,
  privacyRequest,
}: LogDrawerProps) => {
  const headerText = isViewingError ? "Event detail" : "Event log";

  return (
    <Drawer
      open={isOpen}
      onClose={onClose}
      width="50vw"
      autoFocus={false}
      destroyOnHidden
      title={
        <Flex align="center" gap="small">
          {isViewingError && (
            <Button
              icon={<Icons.ArrowLeft />}
              aria-label="Close error logs"
              size="small"
              onClick={onCloseErrorPanel}
            />
          )}
          <span>{headerText}</span>
        </Flex>
      }
    >
      <section
        data-testid="log-drawer"
        id="drawerBody"
        style={{ overflow: "hidden", height: "100%" }}
      >
        {currentLogs && !isViewingError ? (
          <EventLog
            eventLogs={currentLogs}
            allEventLogs={allEventLogs}
            onDetailPanel={onOpenErrorPanel}
            privacyRequest={privacyRequest}
          />
        ) : null}
        {isViewingError ? (
          <EventDetail errorMessage={errorMessage} status={currentStatus} />
        ) : null}
      </section>
    </Drawer>
  );
};

export default LogDrawer;
