import { DataFlowAccordion } from "common/system-data-flow/DataFlowAccordion";
import {
  AntButton as Button,
  Box,
  CloseIcon,
  Flex,
  Slide,
  Spacer,
  Text,
} from "fidesui";
import React, { useMemo } from "react";

import { usePrivacyDeclarationData } from "~/features/system/privacy-declarations/hooks";
import PrivacyDeclarationManager from "~/features/system/privacy-declarations/PrivacyDeclarationManager";
import { useGetSystemByFidesKeyQuery } from "~/features/system/system.slice";

import SystemInfo from "./SystemInfo";

type DatamapDrawerProps = {
  selectedSystemId?: string;
  resetSelectedSystemId: () => void;
};

const DatamapDrawer = ({
  selectedSystemId,
  resetSelectedSystemId,
}: DatamapDrawerProps) => {
  const isOpen = useMemo(() => Boolean(selectedSystemId), [selectedSystemId]);
  const { isLoading, ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: false,
    includeDisabled: false,
  });

  const { data: system } = useGetSystemByFidesKeyQuery(selectedSystemId!, {
    skip: !selectedSystemId,
  });

  return (
    <Box
      position="absolute"
      pointerEvents="none"
      top={0}
      left={0}
      right={0}
      bottom={0}
      overflow="hidden"
    >
      <Slide
        transition={{
          enter: { ease: "easeInOut", duration: 0.5 },
          exit: { ease: "easeInOut", duration: 0.5 },
        }}
        direction="right"
        in={isOpen}
        unmountOnExit
        style={{
          zIndex: 11,
          pointerEvents: "none",
          position: "absolute",
        }}
      >
        <Box
          position="absolute"
          right="0px"
          height="100%"
          width="100%"
          maxWidth="480px"
          pointerEvents="auto"
          borderWidth={0}
          boxShadow="0px 20px 25px -5px rgba(0, 0, 0, 0.1), 0px 10px 10px -5px rgba(0, 0, 0, 0.04)"
          display={selectedSystemId ? "unset" : "none"}
          backgroundColor="white"
          data-testid="datamap-drawer"
        >
          <Box
            id="drawer-header"
            borderBottomWidth={1}
            paddingX={6}
            paddingY={3}
          >
            <Flex>
              <Flex
                justifyContent="space-between"
                alignItems="center"
                height="40px"
              >
                <Text
                  fontWeight="semibold"
                  fontSize="lg"
                  lineHeight="7"
                  color="gray.900"
                >
                  {system?.name ?? "System Information"}
                </Text>
              </Flex>
              <Spacer />
              <Flex alignItems="center">
                <Button
                  icon={<CloseIcon />}
                  aria-label="Close error message"
                  type="text"
                  onClick={resetSelectedSystemId}
                  data-testid="datamap-drawer-close"
                />
              </Flex>
            </Flex>
          </Box>
          <Box
            id="drawer-body"
            height="calc(100% - 46px)"
            overflowY="auto"
            padding={6}
            style={{ scrollbarGutter: "stable" }}
          >
            {system ? (
              <>
                <SystemInfo system={system} />
                <Text
                  size="md"
                  color="gray.600"
                  lineHeight={6}
                  fontWeight="semibold"
                  mt="10px"
                  mb={2}
                >
                  Data uses
                </Text>
                <Box borderTop="1px solid" borderColor="gray.200">
                  <Box pb={3}>
                    <PrivacyDeclarationManager system={system} {...dataProps} />
                  </Box>
                </Box>
                <Text
                  size="md"
                  color="gray.600"
                  lineHeight={6}
                  fontWeight="semibold"
                  mt="10px"
                  mb={2}
                  paddingBottom={2}
                >
                  Data flow
                </Text>
                <DataFlowAccordion system={system} />
              </>
            ) : null}
          </Box>
        </Box>
      </Slide>
    </Box>
  );
};

export default DatamapDrawer;
