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
import { ExecutionLog } from "privacy-requests/types";
import React from "react";

import EventError from "./EventError";
import EventLog from "./EventLog";

type LogDrawerProps = {
  isOpen: boolean;
  onClose: () => void;
  currentLogs: ExecutionLog[];
  isViewingError: boolean;
  errorMessage: string;
  onCloseErrorPanel: () => void;
  onOpenErrorPanel: (message: string) => void;
};

const LogDrawer = ({
  isOpen,
  onClose,
  currentLogs,
  isViewingError,
  errorMessage,
  onCloseErrorPanel,
  onOpenErrorPanel,
}: LogDrawerProps) => {
  const headerText = isViewingError ? "Event detail" : "Event log";

  return (
    <Drawer
      isOpen={isOpen}
      placement="right"
      onClose={onClose}
      size="full"
      autoFocus={false}
    >
      <DrawerOverlay />
      <DrawerContent style={{ width: "50%" }}>
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
            />
          </Flex>
        </DrawerHeader>
        <DrawerBody id="drawerBody" overflow="hidden">
          {currentLogs && !isViewingError ? (
            <EventLog
              eventLogs={currentLogs}
              openErrorPanel={onOpenErrorPanel}
            />
          ) : null}
          {isViewingError ? <EventError errorMessage={errorMessage} /> : null}
        </DrawerBody>
      </DrawerContent>
    </Drawer>
  );
};

export default LogDrawer;
