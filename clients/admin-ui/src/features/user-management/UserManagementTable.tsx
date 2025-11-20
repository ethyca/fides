import {
  AntButton as Button,
  AntFlex as Flex,
  AntTable as Table,
} from "fidesui";
import NextLink from "next/link";
import React, { useEffect } from "react";

import { useAppDispatch } from "~/app/hooks";
import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
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
          <NextLink
            href={`${USER_MANAGEMENT_ROUTE}/new`}
            passHref
            legacyBehavior
          >
            <Button type="primary" data-testid="add-new-user-btn">
              Add new user
            </Button>
          </NextLink>
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
