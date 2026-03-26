import { Button, Flex, Table } from "fidesui";
import { useRouter } from "next/router";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { DATA_CONSUMERS_NEW_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import useDataConsumersTable from "./useDataConsumersTable";

const DataConsumersTable = () => {
  const router = useRouter();
  const { tableProps, columns, searchQuery, updateSearch } =
    useDataConsumersTable();

  return (
    <Flex vertical gap="middle">
      <Flex justify="space-between" className="mb-2">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search data consumers..."
        />
        <Restrict scopes={[ScopeRegistryEnum.DATA_CONSUMER_CREATE]}>
          <Button
            type="primary"
            onClick={() => router.push(DATA_CONSUMERS_NEW_ROUTE)}
            data-testid="add-data-consumer-button"
          >
            Add data consumer
          </Button>
        </Restrict>
      </Flex>
      <Table
        {...tableProps}
        columns={columns}
        data-testid="data-consumers-table"
      />
    </Flex>
  );
};

export default DataConsumersTable;
