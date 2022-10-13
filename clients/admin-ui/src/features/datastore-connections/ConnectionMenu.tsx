import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Portal,
} from "@fidesui/react";
import { MoreIcon } from "common/Icon";
import NextLink from "next/link";
import React from "react";

import { DATASTORE_CONNECTION_ROUTE } from "~/constants";
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
    <MenuButton as={Button} size="xs" bg="white">
      <MoreIcon color="gray.700" w={18} h={18} />
    </MenuButton>
    <Portal>
      <MenuList fontSize="sm" shadow="xl">
        <NextLink
          href={`${DATASTORE_CONNECTION_ROUTE}/${encodeURIComponent(
            connection_key
          )}`}
        >
          <MenuItem _focus={{ color: "complimentary.500", bg: "gray.100" }}>
            Configure
          </MenuItem>
        </NextLink>
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
