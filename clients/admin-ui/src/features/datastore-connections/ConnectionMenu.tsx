import { Button, Menu, MenuButton, MenuList, Portal } from "@fidesui/react";
import React from "react";

import { MoreIcon } from "../common/Icon";
import DeleteConnectionModal from "./DeleteConnectionModal";
import DisableConnectionModal from "./DisableConnectionModal";
import { AccessLevel, ConnectionType } from "./types";

interface ConnectionMenuProps {
  connection_key: string;
  disabled: boolean;
  name: string;
  connection_type: ConnectionType;
  access_type: AccessLevel;
}

const ConnectionMenu: React.FC<ConnectionMenuProps> = ({
  connection_key,
  disabled,
  connection_type,
  access_type,
  name,
}) => (
  <Menu>
    <MenuButton as={Button} size="xs" bg="white">
      <MoreIcon color="gray.700" w={18} h={18} />
    </MenuButton>
    <Portal>
      <MenuList shadow="xl">
        <DisableConnectionModal
          connection_key={connection_key}
          disabled={disabled}
          connection_type={connection_type}
          access_type={access_type}
          name={name}
        />
        <DeleteConnectionModal connection_key={connection_key} />
      </MenuList>
    </Portal>
  </Menu>
);

export default ConnectionMenu;
