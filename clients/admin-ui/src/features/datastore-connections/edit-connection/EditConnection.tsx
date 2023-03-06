import { Box, Flex, Heading, Text, VStack } from "@fidesui/react";
import React, { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import DataTabs, { TabData } from "~/features/common/DataTabs";
import {
  reset,
  selectConnectionTypeState,
  setStep,
} from "~/features/connection-type";

import Breadcrumb from "../add-connection/Breadcrumb";
import ConfigurationSettingsNav from "../add-connection/ConfigurationSettingsNav";
import { ConnectorParameters } from "../add-connection/ConnectorParameters";
import {
  ConfigurationSettings,
  CONNECTOR_PARAMETERS_OPTIONS,
  STEPS,
} from "../add-connection/constants";
import DatasetConfiguration from "../add-connection/DatasetConfiguration";
import DSRCustomization from "../add-connection/manual/DSRCustomization";
import { ConnectorParameterOption } from "../add-connection/types";
import ConnectionTypeLogo from "../ConnectionTypeLogo";

const EditConnection: React.FC = () => {
  const dispatch = useAppDispatch();
  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState
  );
  const [connector, setConnector] = useState(
    undefined as unknown as ConnectorParameterOption
  );
  const [selectedItem, setSelectedItem] = useState("");

  const getTabs = useMemo(
    () => () => {
      const result: TabData[] = [];
      if (connector?.options) {
        connector.options.forEach((option) => {
          let data: TabData | undefined;
          switch (option) {
            case ConfigurationSettings.CONNECTOR_PARAMETERS:
              data = {
                label: option,
                content: <ConnectorParameters />,
              };
              break;
            case ConfigurationSettings.DATASET_CONFIGURATION:
              data = connection?.key
                ? {
                    label: option,
                    content: <DatasetConfiguration />,
                  }
                : undefined;
              break;
            case ConfigurationSettings.DSR_CUSTOMIZATION:
              data = connection?.key
                ? {
                    label: option,
                    content: <DSRCustomization />,
                  }
                : undefined;
              break;
            default:
              break;
          }
          if (data) {
            result.push(data);
          }
        });
      }
      return result;
    },
    [connection?.key, connector?.options]
  );

  const handleNavChange = (value: string) => {
    setSelectedItem(value);
  };

  useEffect(() => {
    if (connectionOption) {
      const item = CONNECTOR_PARAMETERS_OPTIONS.find(
        (o) => o.type === connectionOption?.type
      );
      if (item) {
        setConnector(item);
        setSelectedItem(item.options[0]);
        dispatch(setStep(STEPS[2]));
      }
    }
    return () => {
      // Reset the connection type slice to its initial state
      dispatch(reset());
    };
  }, [connectionOption, dispatch]);

  return connection && connectionOption ? (
    <>
      <Heading
        fontSize="2xl"
        fontWeight="semibold"
        maxHeight="40px"
        mb="4px"
        whiteSpace="nowrap"
      >
        <Box alignItems="center" display="flex">
          <ConnectionTypeLogo data={connection} />
          <Text ml="8px">{connection.name}</Text>
        </Box>
      </Heading>
      <Breadcrumb steps={[STEPS[0], STEPS[2]]} />
      <VStack alignItems="stretch" flex="1" gap="18px">
        <DataTabs data={getTabs()} flexGrow={1} isLazy />
      </VStack>
    </>
  ) : null;
};

export default EditConnection;
