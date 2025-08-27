import {
  AntTabs as Tabs,
  AntTabsProps as TabsProps,
  Box,
  Heading,
  Text,
  VStack,
} from "fidesui";
import React, { useEffect, useMemo, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";
import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  reset,
  selectConnectionTypeState,
  setStep,
} from "~/features/connection-type";

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

const EditConnection = () => {
  const dispatch = useAppDispatch();
  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState,
  );
  const [connector, setConnector] = useState(
    undefined as unknown as ConnectorParameterOption,
  );

  const tabData = useMemo(() => {
    const result: TabsProps["items"] = [];
    if (connector?.options) {
      connector.options.forEach((option) => {
        let data: NonNullable<TabsProps["items"]>[number] | undefined;
        switch (option) {
          case ConfigurationSettings.CONNECTOR_PARAMETERS:
            data = {
              label: option,
              key: option,
              children: <ConnectorParameters />,
            };
            break;
          case ConfigurationSettings.DATASET_CONFIGURATION:
            data = connection?.key
              ? {
                  label: option,
                  key: option,
                  children: <DatasetConfiguration />,
                }
              : undefined;
            break;
          case ConfigurationSettings.DSR_CUSTOMIZATION:
            data = connection?.key
              ? {
                  label: option,
                  key: option,
                  children: <DSRCustomization />,
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
  }, [connection?.key, connector?.options]);

  useEffect(() => {
    if (connectionOption) {
      const item = CONNECTOR_PARAMETERS_OPTIONS.find(
        (o) => o.type === connectionOption?.type,
      );
      if (item) {
        setConnector(item);
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
      <PageHeader
        heading="Connection manager"
        breadcrumbItems={[
          { title: "All connections", href: DATASTORE_CONNECTION_ROUTE },
          { title: connection.name },
        ]}
      />
      <Heading
        fontSize="md"
        fontWeight="semibold"
        maxHeight="40px"
        mb="4px"
        whiteSpace="nowrap"
      >
        <Box alignItems="center" display="flex">
          <ConnectionTypeLogo data={connectionOption} />
          <Text ml="8px">{connection.name}</Text>
        </Box>
      </Heading>
      <VStack alignItems="stretch" flex="1" gap="18px">
        <Tabs items={tabData} />
      </VStack>
    </>
  ) : null;
};

export default EditConnection;
