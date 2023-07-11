import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  MoreIcon,
  Portal,
} from "@fidesui/react";
import NextLink from "next/link";
import React from "react";

import { DATASTORE_CONNECTION_ROUTE } from "~/features/common/nav/v2/routes";
import { ConnectionType } from "~/types/api";

import { AccessLevel } from "./constants";
import DeleteConnectionModal from "./DeleteConnectionModal";
import DisableConnectionModal from "./DisableConnectionModal";

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
      data-testid="connection-menu-btn"
    >
      <MoreIcon color="gray.700" w={18} h={18} />
    </MenuButton>
    <Portal>
      <MenuList
        fontSize="sm"
        shadow="xl"
        data-testid={`connection-menu-${name}`}
      >
        <NextLink
          href={`${DATASTORE_CONNECTION_ROUTE}/${encodeURIComponent(
            connection_key
          )}`}
        >
          <MenuItem
            _focus={{ color: "complimentary.500", bg: "gray.100" }}
            data-testid="configure-btn"
          >
            Configure
          </MenuItem>
        </NextLink>
        <DisableConnectionModal
          connection_key={connection_key}
          disabled={disabled}
          connection_type={connection_type}
          access_type={access_type}
          name={name}
          isSwitch={false}
        />
        <DeleteConnectionModal connection_key={connection_key} />
      </MenuList>
    </Portal>
  </Menu>
);

export default ConnectionMenu;
