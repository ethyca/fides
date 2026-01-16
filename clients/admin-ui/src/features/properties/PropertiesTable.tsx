import { Button, Flex, Table } from "fidesui";
import { useRouter } from "next/router";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import ErrorPage from "~/features/common/errors/ErrorPage";
import { ADD_PROPERTY_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import usePropertiesTable from "~/features/properties/usePropertiesTable";
import { ScopeRegistryEnum } from "~/types/api";

const PropertiesTable = () => {
  const { tableProps, columns, searchQuery, updateSearch, error } =
    usePropertiesTable();

  const router = useRouter();

  if (error) {
    return (
      <ErrorPage
        error={error}
        defaultMessage="A problem occurred while fetching properties"
      />
    );
  }

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
            data-testid="add-property-button"
          >
            Add a property
          </Button>
        </Restrict>
      </Flex>
      <Table {...tableProps} columns={columns} data-testid="properties-table" />
    </Flex>
  );
};

export default PropertiesTable;
