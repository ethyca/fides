import {
  Box,
  Heading,
  IconButton,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
} from "@fidesui/react";

import { MoreIcon } from "~/features/common/Icon";
import { System } from "~/types/api";

interface SystemCardProps {
  system: System;
}
const SystemCard = ({ system }: SystemCardProps) => {
  // TODO fides#1035, fides#1036
  const handleEdit = () => {};
  const handleDelete = () => {};

  return (
    <Box display="flex" p={4} data-testid={`system-${system.fides_key}`}>
      <Box flexGrow={1}>
        <Heading as="h2" fontSize="16px" mb={2}>
          {system.name}
        </Heading>
        <Box color="gray.600" fontSize="14px">
          <Text>{system.description}</Text>
        </Box>
      </Box>
      <Menu>
        <MenuButton
          as={IconButton}
          icon={<MoreIcon />}
          aria-label="more actions"
          variant="unstyled"
          size="sm"
          data-testid="more-btn"
        />
        <MenuList>
          <MenuItem onClick={handleEdit} data-testid="edit-btn">
            Edit
          </MenuItem>
          <MenuItem onClick={handleDelete} data-testid="delete-btn">
            Delete
          </MenuItem>
        </MenuList>
      </Menu>
    </Box>
  );
};

export default SystemCard;
