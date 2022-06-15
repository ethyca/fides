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
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { User } from "./types";
import {
  selectUserFilters,
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

  return (
    <>
      <Table size="sm">
        <Thead>
          <Tr>
            <Th pl={0}>Username</Th>
            <Th pl={0}>First Name</Th>
            <Th pl={0}>Last Name</Th>
            <Th pl={0}>Created At</Th>
          </Tr>
        </Thead>
        <Tbody>
          {users?.map((user) => (
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
