import { Box } from "@fidesui/react";
import { useMemo, useState } from "react";

import BorderGrid from "~/features/common/BorderGrid";
import SearchBar from "~/features/common/SearchBar";
import SystemCard from "~/features/system/SystemCard";
import { System } from "~/types/api";

export const SEARCH_FILTER = (system: System, search: string) =>
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
    return <div data-testid="empty-state">No systems registered.</div>;
  }

  return (
    <Box data-testid="system-management">
      <Box mb={4} data-testid="system-filters">
        <SearchBar
          search={searchFilter}
          onChange={setSearchFilter}
          maxWidth="30vw"
          placeholder="Search system name or description"
          data-testid="system-search"
          withIcon
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
