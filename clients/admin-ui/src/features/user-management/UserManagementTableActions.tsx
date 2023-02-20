import { Button, Stack } from "@fidesui/react";
import NextLink from "next/link";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { USER_MANAGEMENT_ROUTE } from "~/constants";
import SearchBar from "~/features/common/SearchBar";

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

const UserManagementTableActions: React.FC = () => {
  const { handleSearchChange, username } = useUserManagementTableActions();

  return (
    <Stack direction="row" spacing={4} mb={6}>
      <SearchBar
        search={username}
        onChange={handleSearchChange}
        placeholder="Search by Username"
      />
      <NextLink href={`${USER_MANAGEMENT_ROUTE}/new`} passHref>
        <Button colorScheme="primary" flexShrink={0} size="sm">
          Add New User
        </Button>
      </NextLink>
    </Stack>
  );
};

export default UserManagementTableActions;
