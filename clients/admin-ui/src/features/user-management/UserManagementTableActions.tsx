import { Button, Stack } from "fidesui";
import NextLink from "next/link";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { USER_MANAGEMENT_ROUTE } from "~/features/common/nav/v2/routes";
import Restrict from "~/features/common/Restrict";
import SearchBar from "~/features/common/SearchBar";
import { ScopeRegistryEnum } from "~/types/api";

import { selectUserFilters, setUsernameSearch } from "./user-management.slice";

const useUserManagementTableActions = () => {
  const filters = useSelector(selectUserFilters);
  const dispatch = useDispatch();
  const handleSearchChange = (value: string) => {
    dispatch(setUsernameSearch(value));
  };

  return {
    handleSearchChange,
    ...filters,
  };
};

const UserManagementTableActions = () => {
  const { handleSearchChange, username } = useUserManagementTableActions();

  return (
    <Stack direction="row" spacing={4} mb={6}>
      <SearchBar
        search={username}
        onChange={handleSearchChange}
        placeholder="Search by Username"
      />
      <Restrict scopes={[ScopeRegistryEnum.USER_CREATE]}>
        <Button
          as={NextLink}
          href={`${USER_MANAGEMENT_ROUTE}/new`}
          colorScheme="primary"
          flexShrink={0}
          size="sm"
          data-testid="add-new-user-btn"
        >
          Add new user
        </Button>
      </Restrict>
    </Stack>
  );
};

export default UserManagementTableActions;
