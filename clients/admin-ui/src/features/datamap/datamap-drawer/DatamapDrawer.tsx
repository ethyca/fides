import { ChakraBox as Box, ChakraText as Text, Drawer } from "fidesui";
import React, { useMemo } from "react";

import { DataFlowAccordion } from "~/features/common/system-data-flow/DataFlowAccordion";
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
  const { ...dataProps } = usePrivacyDeclarationData({
    includeDatasets: false,
    includeDisabled: false,
  });

  const { data: system, isLoading } = useGetSystemByFidesKeyQuery(
    selectedSystemId!,
    {
      skip: !selectedSystemId,
    },
  );

  return (
    <Drawer
      open={isOpen}
      onClose={resetSelectedSystemId}
      placement="right"
      width={480}
      title={system?.name ?? "System Information"}
      loading={isLoading}
    >
      {system ? (
        <div data-testid="datamap-drawer">
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
        </div>
      ) : null}
    </Drawer>
  );
};

export default DatamapDrawer;
