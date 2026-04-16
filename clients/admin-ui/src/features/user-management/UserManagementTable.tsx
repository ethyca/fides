import { Button, Flex, Table } from "fidesui";
import React, { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/routes";
import Restrict from "~/features/common/Restrict";
import { ScopeRegistryEnum } from "~/types/api";

import { setActiveUserId } from "./user-management.slice";
import useUserManagementTable from "./useUserManagementTable";

const UserManagementTable = () => {
  const { tableProps, columns, searchQuery, updateSearch } =
    useUserManagementTable();
  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(setActiveUserId(undefined));
  }, [dispatch]);

  return (
    <>
      <Flex justify="space-between" className="mb-4">
        <DebouncedSearchInput
          value={searchQuery}
          onChange={updateSearch}
          placeholder="Search by username"
          data-testid="user-search"
        />
        <Restrict scopes={[ScopeRegistryEnum.USER_CREATE]}>
          <RouterLink href={`${USER_MANAGEMENT_ROUTE}/new`}>
            <Button type="primary" data-testid="add-new-user-btn">
              Add new user
            </Button>
          </RouterLink>
        </Restrict>
      </Flex>
      <Table
        {...tableProps}
        columns={columns}
        data-testid="user-management-table"
        onRow={(user) =>
          ({
            "data-testid": `row-${user.id}`,
          }) as React.HTMLAttributes<HTMLTableRowElement>
        }
      />
    </>
  );
};

export default UserManagementTable;
