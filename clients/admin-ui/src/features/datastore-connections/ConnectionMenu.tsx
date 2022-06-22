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

interface ConnectionMenuProps {
  // disabled: boolean;
}

const ConnectionMenu: React.FC<ConnectionMenuProps> = () => (
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
        <MenuItem
          _focus={{ color: "complimentary.500", bg: "gray.100" }}
          // onClick={handleViewDetails}
        >
          <Text fontSize="sm">Disable</Text>
        </MenuItem>
        <MenuItem
          _focus={{ color: "complimentary.500", bg: "gray.100" }}
          // onClick={handleViewDetails}
        >
          <Text fontSize="sm">Delete</Text>
        </MenuItem>
      </MenuList>
    </Portal>
  </Menu>
);

export default ConnectionMenu;
