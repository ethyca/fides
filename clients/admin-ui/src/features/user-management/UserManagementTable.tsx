import { AntButton, Flex, Table, Tbody, Text, Th, Thead, Tr } from "fidesui";
import React, { useEffect } from "react";
import { useDispatch, useSelector } from "react-redux";

import { useAppDispatch } from "~/app/hooks";

import {
  selectUserFilters,
  setActiveUserId,
  setPage,
  useGetAllUsersQuery,
} from "./user-management.slice";
import UserManagementRow from "./UserManagementRow";

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
  const users = data?.items ?? [];
  const total = data?.total ?? 0;

  return {
    ...filters,
    isLoading,
    users,
    total,
    handleNextPage,
    handlePreviousPage,
  };
};

const UserManagementTable = () => {
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
            <Th pl={0}>Email</Th>
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
          <AntButton
            disabled={page <= 1}
            onClick={handlePreviousPage}
            className="mr-2"
          >
            Previous
          </AntButton>
          <AntButton disabled={page * size >= total} onClick={handleNextPage}>
            Next
          </AntButton>
        </div>
      </Flex>
    </>
  );
};

UserManagementTable.defaultProps = {
  users: [],
};

export default UserManagementTable;
