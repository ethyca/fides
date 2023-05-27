import {
  Button,
  Flex,
  Table,
  Tbody,
  Text,
  Th,
  Thead,
  Tr,
} from "@fidesui/react";
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { useAppDispatch } from "~/app/hooks";

import { User } from "./types";
import {
  selectUserFilters,
  setActiveUserId,
  setPage,
  useGetAllUsersQuery,
} from "./user-management.slice";
import UserManagementRow from "./UserManagementRow";

interface UsersTableProps {
  users?: User[];
}

const useUsersTable = () => {
  const dispatch = useDispatch();
  const filters = useSelector(selectUserFilters);

  const handlePreviousPage = () => {
    dispatch(setPage(filters.page - 1));
  };

  const handleNextPage = () => {
    dispatch(setPage(filters.page + 1));
  };

  const { data, isLoading } = useGetAllUsersQuery(filters);
  const { items: users, total } = data || { users: [], total: 0 };

  return {
    ...filters,
    isLoading,
    users,
    total,
    handleNextPage,
    handlePreviousPage,
  };
};

const UserManagementTable: React.FC<UsersTableProps> = () => {
  const { users, total, page, size, handleNextPage, handlePreviousPage } =
    useUsersTable();
  const startingItem = (page - 1) * size + 1;
  const endingItem = Math.min(total, page * size);

  const dispatch = useAppDispatch();

  useEffect(() => {
    dispatch(setActiveUserId(undefined));
  }, [dispatch]);

  return (
    <>
      <Table size="sm" data-testid="user-management-table">
        <Thead>
          <Tr>
            <Th pl={0}>Username</Th>
            <Th pl={0}>First Name</Th>
            <Th pl={0}>Last Name</Th>
            <Th pl={0}>Permissions</Th>
            <Th pl={0}>Assigned Systems</Th>
            <Th pl={0}>Created At</Th>
          </Tr>
        </Thead>
        <Tbody>
          {users?.map((user: any) => (
            <UserManagementRow user={user} key={user.id} />
          ))}
        </Tbody>
      </Table>
      <Flex justifyContent="space-between" mt={6}>
        <Text fontSize="xs" color="gray.600">
          {total > 0 ? (
            <>
              Showing {Number.isNaN(startingItem) ? 0 : startingItem} to{" "}
              {Number.isNaN(endingItem) ? 0 : endingItem} of{" "}
              {Number.isNaN(total) ? 0 : total} results
            </>
          ) : (
            "0 results"
          )}
        </Text>
        <div>
          <Button
            disabled={page <= 1}
            onClick={handlePreviousPage}
            mr={2}
            size="sm"
          >
            Previous
          </Button>
          <Button
            disabled={page * size >= total}
            onClick={handleNextPage}
            size="sm"
          >
            Next
          </Button>
        </div>
      </Flex>
    </>
  );
};

UserManagementTable.defaultProps = {
  users: [],
};

export default UserManagementTable;
