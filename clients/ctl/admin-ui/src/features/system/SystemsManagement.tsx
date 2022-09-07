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
import { useMemo, useState } from "react";

import BorderGrid from "~/features/common/BorderGrid";
import { MoreIcon } from "~/features/common/Icon";
import { System } from "~/types/api";

import SearchBar from "../common/SearchBar";

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
        />
        <MenuList>
          <MenuItem onClick={handleEdit}>Edit</MenuItem>
          <MenuItem onClick={handleDelete}>Delete</MenuItem>
        </MenuList>
      </Menu>
    </Box>
  );
};

const SEARCH_FILTER = (system: System, search: string) =>
  system.name?.toLocaleLowerCase().includes(search.toLocaleLowerCase()) ||
  system.description?.toLocaleLowerCase().includes(search.toLocaleLowerCase());

interface Props {
  systems: System[] | undefined;
}
const SystemsManagement = ({ systems }: Props) => {
  const [searchFilter, setSearchFilter] = useState("");

  const filteredSystems = useMemo(() => {
    if (!systems) {
      return [];
    }

    return systems.filter((s) => SEARCH_FILTER(s, searchFilter));
  }, [systems, searchFilter]);

  if (!systems || !systems.length) {
    return <div data-testid="empty-state">Empty state</div>;
  }

  return (
    <Box>
      <Box mb={4} data-testid="system-filters">
        <SearchBar
          search={searchFilter}
          onChange={setSearchFilter}
          maxWidth="30vw"
        />
      </Box>
      <BorderGrid<System>
        columns={3}
        items={filteredSystems}
        renderItem={(system) => <SystemCard system={system} />}
      />
    </Box>
  );
};

export default SystemsManagement;
