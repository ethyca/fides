import { Flex } from "@fidesui/react";
import { useAppSelector } from "app/hooks";
import {
  selectConnectionTypeState,
  setConnection,
  setStep,
} from "connection-type/connection-type.slice";
import { SystemType } from "datastore-connections/constants";
import React, { useCallback, useEffect, useRef, useState } from "react";
import { useDispatch } from "react-redux";

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

  const { connection, connectionOption, step } = useAppSelector(
    selectConnectionTypeState
  );

  const connector = CONNECTOR_PARAMETERS_OPTIONS.find(
    (o) => o.type === connectionOption?.type
  );
  const [selectedItem, setSelectedItem] = useState(connector?.options[0]);

  const handleConnectionCreated = () => {
    setCanRedirect(true);
  };

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
      // Reset the connection state when the component is unmounted
      dispatch(setConnection(undefined));
    };
  }, [dispatch]);

  useEffect(() => {
    if (step) {
      setSelectedItem(
        connector?.options[Number(step.stepId) - connector.options.length]
      );
    }

    // If a connection has been initially created, then auto redirect the user accordingly.
    if (connection?.key && canRedirect) {
      handleNavChange(
        connectionOption?.type !== SystemType.MANUAL
          ? ConfigurationSettings.DATASET_CONFIGURATION
          : ConfigurationSettings.DSR_CUSTOMIZATION
      );
      setCanRedirect(false);
    }
  }, [
    canRedirect,
    connection?.key,
    connectionOption?.type,
    connector?.options,
    handleNavChange,
    step,
  ]);

  return (
    <>
      <Breadcrumb steps={steps} />
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
    </>
  );
};

export default ConfigureConnector;
