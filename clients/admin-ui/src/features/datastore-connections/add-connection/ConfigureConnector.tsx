import { Flex, VStack } from "@fidesui/react";
import {
  reset,
  selectConnectionTypeState,
  setStep,
} from "connection-type/connection-type.slice";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";
import DataTabs, { TabData } from "~/features/common/DataTabs";
import { useFeatures } from "~/features/common/features";
import { SystemType } from "~/types/api";

import Breadcrumb from "./Breadcrumb";
import ConfigurationSettingsNav from "./ConfigurationSettingsNav";
import { ConnectorParameters } from "./ConnectorParameters";
import {
  ConfigurationSettings,
  CONNECTOR_PARAMETERS_OPTIONS,
  STEPS,
} from "./constants";
import DatasetConfiguration from "./DatasetConfiguration";
import DSRCustomization from "./manual/DSRCustomization";

const ConfigureConnector: React.FC = () => {
  const dispatch = useDispatch();
  const mounted = useRef(false);
  const [steps, setSteps] = useState([STEPS[0], STEPS[1], STEPS[2]]);
  const [canRedirect, setCanRedirect] = useState(false);
  const { connection, connectionOption } = useAppSelector(
    selectConnectionTypeState
  );
  const connector = CONNECTOR_PARAMETERS_OPTIONS.find(
    (o) => o.type === connectionOption?.type
  );
  const [selectedItem, setSelectedItem] = useState(connector?.options[0]);
  const {
    flags: { navV2 },
  } = useFeatures();

  const handleConnectionCreated = () => {
    setCanRedirect(true);
  };

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
                content: (
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

  const handleNavChange = useCallback(
    (value: string) => {
      switch (value) {
        case ConfigurationSettings.DATASET_CONFIGURATION:
        case ConfigurationSettings.DSR_CUSTOMIZATION:
          dispatch(setStep(STEPS[3]));
          setSteps([STEPS[0], STEPS[1], STEPS[3]]);
          break;
        case ConfigurationSettings.CONNECTOR_PARAMETERS:
        default:
          dispatch(setStep(STEPS[2]));
          break;
      }
      setSelectedItem(value);
    },
    [dispatch]
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
          : ConfigurationSettings.DSR_CUSTOMIZATION
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
    <>
      <Breadcrumb steps={steps} />
      {navV2 && (
        <VStack alignItems="stretch" gap="18px">
          <DataTabs
            data={getTabs()}
            flexGrow={1}
            index={connector?.options.findIndex(
              (option) => option === selectedItem
            )}
            isLazy
          />
        </VStack>
      )}
      {!navV2 && (
        <Flex flex="1" gap="18px">
          <ConfigurationSettingsNav
            menuOptions={connector?.options || []}
            onChange={handleNavChange}
            selectedItem={selectedItem || ""}
          />
          {(() => {
            switch (selectedItem || "") {
              case ConfigurationSettings.CONNECTOR_PARAMETERS:
                return (
                  <ConnectorParameters
                    onConnectionCreated={handleConnectionCreated}
                  />
                );
              case ConfigurationSettings.DATASET_CONFIGURATION:
                return <DatasetConfiguration />;
              case ConfigurationSettings.DSR_CUSTOMIZATION:
                return <DSRCustomization />;
              default:
                return null;
            }
          })()}
        </Flex>
      )}
    </>
  );
};

export default ConfigureConnector;
