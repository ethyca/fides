import {
  reset,
  selectConnectionTypeState,
  setStep,
} from "connection-type/connection-type.slice";
import { AntTabs as Tabs, AntTabsProps as TabsProps, VStack } from "fidesui";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import { SystemType } from "~/types/api";

import { ConnectorParameters } from "./ConnectorParameters";
import {
  ConfigurationSettings,
  CONNECTOR_PARAMETERS_OPTIONS,
  STEPS,
} from "./constants";
import DatasetConfiguration from "./DatasetConfiguration";
import DSRCustomization from "./manual/DSRCustomization";

const ConfigureConnector = () => {
  const dispatch = useDispatch();
  const mounted = useRef(false);
  const [canRedirect, setCanRedirect] = useState(false);
  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState,
  );
  const connector = CONNECTOR_PARAMETERS_OPTIONS.find(
    (o) => o.type === connectionOption?.type,
  );
  const [selectedItem, setSelectedItem] = useState(connector?.options[0]);

  const handleConnectionCreated = () => {
    setCanRedirect(true);
  };

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
              children: (
                <ConnectorParameters
                  onConnectionCreated={handleConnectionCreated}
                />
              ),
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

  const handleNavChange = useCallback(
    (value: string) => {
      switch (value) {
        case ConfigurationSettings.DATASET_CONFIGURATION:
        case ConfigurationSettings.DSR_CUSTOMIZATION:
          dispatch(setStep(STEPS[3]));
          break;
        case ConfigurationSettings.CONNECTOR_PARAMETERS:
        default:
          dispatch(setStep(STEPS[2]));
          break;
      }
      setSelectedItem(value);
    },
    [dispatch],
  );

  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
      // Reset the connection type slice to its initial state
      dispatch(reset());
    };
  }, [dispatch]);

  useEffect(() => {
    // If a connection has been initially created, then auto redirect the user accordingly.
    if (connection?.key) {
      handleNavChange(
        connectionOption?.type !== SystemType.MANUAL
          ? ConfigurationSettings.DATASET_CONFIGURATION
          : ConfigurationSettings.DSR_CUSTOMIZATION,
      );
      if (canRedirect) {
        setCanRedirect(false);
      }
    }
  }, [
    canRedirect,
    connection?.key,
    connectionOption?.type,
    connector?.options,
    handleNavChange,
  ]);

  return (
    <VStack alignItems="stretch" gap="18px">
      <Tabs
        items={tabData}
        activeKey={selectedItem}
        onChange={handleNavChange}
      />
    </VStack>
  );
};

export default ConfigureConnector;
