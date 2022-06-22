import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Portal,
  Text,
} from "@fidesui/react";
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
    <MenuButton
      as={Button}
      size="xs"
      bg="white"
      // ref={request.status !== "pending" ? hoverButtonRef : null}
    >
      <MoreIcon color="gray.700" w={18} h={18} />
    </MenuButton>
    <Portal>
      <MenuList shadow="xl">
        <MenuItem
          _focus={{ color: "complimentary.500", bg: "gray.100" }}
          // onClick={handleIdCopy}
        >
          <Text fontSize="sm">Edit</Text>
        </MenuItem>
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
