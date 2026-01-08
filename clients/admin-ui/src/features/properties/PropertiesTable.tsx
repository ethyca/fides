import { Button, Flex, Table } from "fidesui";
import { useRouter } from "next/router";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import usePropertiesTable from "~/features/properties/usePropertiesTable";
import { ScopeRegistryEnum } from "~/types/api";

const PropertiesTable = () => {
  const { tableProps, columns, searchQuery, updateSearch } =
    usePropertiesTable();

  const router = useRouter();

  return (
    <Flex vertical gap="small">
      <Flex justify="space-between">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search properties..."
        />
        <Restrict scopes={[ScopeRegistryEnum.PROPERTY_CREATE]}>
          <Button
            type="primary"
            onClick={() => router.push(ADD_PROPERTY_ROUTE)}
          >
            Add a property
          </Button>
        </Restrict>
      </Flex>
      <Table {...tableProps} columns={columns} />
    </Flex>
  );
};

export default PropertiesTable;
