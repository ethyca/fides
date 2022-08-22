import { Flex } from "@fidesui/react";
import { ConnectionOption } from "connection-type/types";
import { SystemType } from "datastore-connections/constants";
import React, { useState } from "react";

import ConfigurationSettingsNav from "./ConfigurationSettingsNav";
import { ConnectorParameters } from "./ConnectorParameters";
import { CONNECTOR_PARAMETERS_OPTIONS } from "./constants";
import DatasetConfiguration from "./sass/DatasetConfiguration";
import { AddConnectionStep } from "./types";

type ConfigureConnectorProps = {
  currentStep: AddConnectionStep;
  connectionOption: ConnectionOption;
};

const ConfigureConnector: React.FC<ConfigureConnectorProps> = ({
  currentStep,
  connectionOption,
}) => {
  const [selectedItem, setSelectedItem] = useState(
    CONNECTOR_PARAMETERS_OPTIONS[0]
  );

  const handleNavChange = (value: string) => {
    setSelectedItem(value);
  };

  return (
    <Flex gap="18px">
      <ConfigurationSettingsNav
        onChange={handleNavChange}
        selectedItem={selectedItem}
      />
      {connectionOption.type === SystemType.SAAS.toString() &&
        selectedItem === CONNECTOR_PARAMETERS_OPTIONS[0] && (
          <ConnectorParameters
            currentStep={currentStep}
            connectionOption={connectionOption}
          />
        )}
      {connectionOption.type === SystemType.SAAS.toString() &&
        selectedItem === CONNECTOR_PARAMETERS_OPTIONS[2] && (
          <DatasetConfiguration
            currentStep={currentStep}
            connectionOption={connectionOption}
          />
        )}
    </Flex>
  );
};

export default ConfigureConnector;
