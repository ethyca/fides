import {
  AntButton as Button,
  ArrowBackIcon,
  CloseSolidIcon,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  Text,
} from "fidesui";
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
      isOpen={isOpen}
      placement="right"
      onClose={onClose}
      size="full"
      autoFocus={false}
      data-testid="log-drawer"
    >
      <DrawerOverlay />
      <DrawerContent style={{ width: "50%" }} data-testid="log-drawer">
        <DrawerHeader style={{ paddingBottom: "0px" }}>
          <Flex
            justifyContent="space-between"
            alignItems="center"
            height="40px"
          >
            <Flex alignItems="center">
              {isViewingError && (
                <Button
                  icon={<ArrowBackIcon />}
                  aria-label="Close error logs"
                  size="small"
                  onClick={onCloseErrorPanel}
                />
              )}
              <Text
                color="gray.900"
                fontSize="md"
                lineHeight="6"
                fontWeight="medium"
                ml={1}
              >
                {headerText}
              </Text>
            </Flex>
            <Button
              icon={<CloseSolidIcon width="17px" />}
              aria-label="Stop viewing error message"
              size="small"
              onClick={onClose}
              data-testid="log-drawer-close"
            />
          </Flex>
        </DrawerHeader>
        <DrawerBody id="drawerBody" overflow="hidden">
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
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
};

export default LogDrawer;
