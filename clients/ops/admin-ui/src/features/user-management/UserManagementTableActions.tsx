import {
  Button,
  Input,
  InputGroup,
  InputLeftElement,
  Stack,
} from "@fidesui/react";
import NextLink from "next/link";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { USER_MANAGEMENT_ROUTE } from "../../constants";
import { SearchLineIcon } from "../common/Icon";
import { selectUserFilters, setUsernameSearch } from "./user-management.slice";

const useUserManagementTableActions = () => {
  const filters = useSelector(selectUserFilters);
  const dispatch = useDispatch();
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    dispatch(setUsernameSearch(event.target.value));
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
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
        <Input
          type="search"
          minWidth={200}
          placeholder="Search by Username"
          size="sm"
          borderRadius="md"
          value={username}
          name="search"
          onChange={handleSearchChange}
        />
      </InputGroup>
      <NextLink href={`${USER_MANAGEMENT_ROUTE}/new`} passHref>
        <Button
          variant="solid"
          bg="primary.800"
          color="white"
          flexShrink={0}
          size="sm"
        >
          Add New User
        </Button>
      </NextLink>
    </Stack>
  );
};

export default UserManagementTableActions;
