import { ArrowBackIcon } from "@chakra-ui/icons";
import { useDisclosure } from "@chakra-ui/react";
import {
  Box,
  Divider,
  Drawer,
  DrawerBody,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  Flex,
  IconButton,
  Text,
} from "@fidesui/react";
import { CloseSolidIcon } from "common/Icon";
import { ExecutionLog } from "privacy-requests/types";
import React, { useState } from "react";

import EventError from "./EventError";
import EventLog from "./EventLog";

export type EventData = {
  key: string;
  logs: ExecutionLog[];
};

type EventDetailsProps = {
  eventData: EventData | undefined;
};

const EventDetails = ({ eventData }: EventDetailsProps) => {
  const { isOpen, onOpen, onClose } = useDisclosure();

  const [isViewingError, setViewingError] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

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

    onClose();
  };

  const headerText = isViewingError ? "Event detail" : "Event log";
  if (eventData === undefined) {
    return null;
  }
  return (
    <Box width="100%" paddingTop="0px" height="100%">
      <Text color="gray.900" fontSize="md" fontWeight="500" mb={1}>
        Event Details
      </Text>

      <Text
        color="gray.600"
        fontSize="sm"
        fontWeight="500"
        lineHeight="20px"
        mb={1}
      >
        {eventData.key}
      </Text>
      <Divider />

      <Text
        cursor="pointer"
        color="complimentary.500"
        fontWeight="500"
        fontSize="sm"
        onClick={() => {
          onOpen();
        }}
      >
        View Log
      </Text>

      <Drawer
        isOpen={isOpen}
        placement="right"
        onClose={closeDrawer}
        size="full"
        autoFocus={false}
      >
        <DrawerOverlay />
        <DrawerContent style={{ width: "50%" }}>
          <DrawerHeader
            style={{
              paddingBottom: "0px",
            }}
          >
            <Flex
              justifyContent="space-between"
              alignItems="center"
              height="40px"
            >
              <Flex alignItems="center">
                {isViewingError ? (
                  <IconButton
                    icon={<ArrowBackIcon />}
                    aria-label="Close error logs"
                    size="sm"
                    style={{
                      height: "24px",
                      width: "24px",
                      minWidth: "24px",
                      marginRight: "8px",
                    }}
                    onClick={closeErrorPanel}
                  />
                ) : null}
                <Text
                  color="gray.900"
                  fontSize="md"
                  lineHeight="6"
                  fontWeight="medium"
                >
                  {headerText}
                </Text>
              </Flex>

              <Flex alignItems="flex-start" height="100%">
                <IconButton
                  icon={<CloseSolidIcon />}
                  aria-label="Stop viewing error message"
                  variant="unstyled"
                  size="sm"
                  style={{
                    height: "24px",
                    width: "24px",
                    minWidth: "14px",
                    backgroundColor: "#00000000",
                  }}
                  isRound
                  onClick={closeDrawer}
                />
              </Flex>
            </Flex>
          </DrawerHeader>
          <DrawerBody id="drawerBody" overflow="hidden">
            {eventData && !isViewingError ? (
              <EventLog
                eventLogs={eventData.logs}
                openErrorPanel={openErrorPanel}
              />
            ) : null}
            {isViewingError ? <EventError errorMessage={errorMessage} /> : null}
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </Box>
  );
};

export default EventDetails;
