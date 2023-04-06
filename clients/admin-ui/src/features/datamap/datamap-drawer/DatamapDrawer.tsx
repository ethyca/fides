import {
  Box,
  CloseIcon,
  Flex,
  IconButton,
  Slide,
  Spacer,
  Text,
  useToast,
} from "@fidesui/react";
import { SerializedError } from "@reduxjs/toolkit";
import { FetchBaseQueryError } from "@reduxjs/toolkit/dist/query/fetchBaseQuery";
import React, { useMemo } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import { useTaxonomyData } from "~/features/datamap/privacy-declarations/PrivacyDeclarationForm";
import PrivacyDeclarationManager from "~/features/datamap/privacy-declarations/PrivacyDeclarationManager";
import {
  useGetSystemByFidesKeyQuery,
  useUpdateSystemMutation,
} from "~/features/system/system.slice";
import { PrivacyDeclaration } from "~/types/api/models/PrivacyDeclaration";
import { System } from "~/types/api/models/System";

import SystemInfo from "./SystemInfo";
import { DataFlowAccordion } from "common/system-data-flow/DataFlowAccordion";

type DatamapDrawerProps = {
  selectedSystemId?: string;
  resetSelectedSystemId: () => void;
};

const DatamapDrawer = ({
  selectedSystemId,
  resetSelectedSystemId,
}: DatamapDrawerProps) => {
  const isOpen = useMemo(() => Boolean(selectedSystemId), [selectedSystemId]);
  const { isLoading, ...dataProps } = useTaxonomyData();
  const toast = useToast();

  const [updateSystemMutationTrigger] = useUpdateSystemMutation();
  const { data: system } = useGetSystemByFidesKeyQuery(selectedSystemId!, {
    skip: !selectedSystemId,
  });

  const handleSave = async (
    updatedDeclarations: PrivacyDeclaration[],
    isDelete?: boolean
  ) => {
    const systemBodyWithDeclaration = {
      ...system!,
      privacy_declarations: updatedDeclarations,
    };

    const handleResult = (
      result:
        | { data: System }
        | { error: FetchBaseQueryError | SerializedError }
    ) => {
      if (isErrorResult(result)) {
        const errorMsg = getErrorMessage(
          result.error,
          "An unexpected error occurred while updating the system. Please try again."
        );

        toast(errorToastParams(errorMsg));
        return false;
      }
      toast.closeAll();
      toast(
        successToastParams(isDelete ? "Data use deleted" : "Data use saved")
      );
      return true;
    };

    const updateSystemResult = await updateSystemMutationTrigger(
      systemBodyWithDeclaration
    );

    return handleResult(updateSystemResult);
  };
  const collisionWarning = () => {
    toast(
      errorToastParams(
        "A declaration already exists with that data use in this system. Please supply a different data use."
      )
    );
  };

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
                <IconButton
                  icon={<CloseIcon />}
                  aria-label="Close error message"
                  size="sm"
                  style={{
                    height: "24px",
                    width: "24px",
                    minWidth: "14px",
                    backgroundColor: "#00000000",
                  }}
                  onClick={resetSelectedSystemId}
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
                  <PrivacyDeclarationManager
                    system={system!}
                    onCollision={collisionWarning}
                    onSave={handleSave}
                    {...dataProps}
                  />
                </Box>
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
