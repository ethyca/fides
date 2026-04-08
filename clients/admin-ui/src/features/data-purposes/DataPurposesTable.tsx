import { Button, Flex, Table } from "fidesui";
import { useRouter } from "next/router";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { DATA_PURPOSES_NEW_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import useDataPurposesTable from "~/features/data-purposes/useDataPurposesTable";
import { ScopeRegistryEnum } from "~/types/api";

interface DataPurposesTableProps {
  searchQuery?: string;
  onSearchChange?: (value: string) => void;
}

const DataPurposesTable = ({
  searchQuery: externalSearchQuery,
  onSearchChange,
}: DataPurposesTableProps) => {
  const router = useRouter();
  const { tableProps, columns, searchQuery, updateSearch } =
    useDataPurposesTable();

  return (
    <Flex vertical gap="middle">
      <Flex justify="space-between" className="mb-2">
        {!onSearchChange && (
          <DebouncedSearchInput
            value={searchQuery}
            onChange={updateSearch}
            placeholder="Search data purposes..."
          />
        )}
        <Restrict scopes={[ScopeRegistryEnum.DATA_PURPOSE_CREATE]}>
          <Button
            type="primary"
            onClick={() => router.push(DATA_PURPOSES_NEW_ROUTE)}
            data-testid="add-data-purpose-button"
          >
            Add data purpose
          </Button>
        </Restrict>
      </Flex>
      <Table
        {...tableProps}
        columns={columns}
        data-testid="data-purposes-table"
      />
    </Flex>
  );
};

export default DataPurposesTable;
