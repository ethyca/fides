import { AntButton, Stack } from "fidesui";
import { useRouter } from "next/router";
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
  const router = useRouter();

  return (
    <Stack direction="row" spacing={4} mb={6}>
      <SearchBar
        search={username}
        onChange={handleSearchChange}
        placeholder="Search by Username"
      />
      <Restrict scopes={[ScopeRegistryEnum.USER_CREATE]}>
        <AntButton
          onClick={() => router.push(`${USER_MANAGEMENT_ROUTE}/new`)}
          type="primary"
          className="shrink-0"
          data-testid="add-new-user-btn"
        >
          Add new user
        </AntButton>
      </Restrict>
    </Stack>
  );
};

export default UserManagementTableActions;
