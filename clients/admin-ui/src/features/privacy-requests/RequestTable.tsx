import {
  Button,
  Flex,
  Table,
  Tbody,
  Text,
  Th,
  Thead,
  Tr,
} from '@fidesui/react';
import debounce from 'lodash.debounce';
import React, { useEffect, useRef, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';

import {
  selectPrivacyRequestFilters,
  setPage,
  useGetAllPrivacyRequestsQuery,
} from './privacy-requests.slice';
import RequestRow from './RequestRow';
import { PrivacyRequest } from './types';

interface RequestTableProps {
  requests?: PrivacyRequest[];
}

const useRequestTable = () => {
  const dispatch = useDispatch();
  const filters = useSelector(selectPrivacyRequestFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const updateCachedFilters = useRef(
    debounce((updatedFilters) => setCachedFilters(updatedFilters), 250)
  );
  useEffect(() => {
    updateCachedFilters.current(filters);
  }, [setCachedFilters, filters]);

  const handlePreviousPage = () => {
    dispatch(setPage(filters.page - 1));
  };

  const handleNextPage = () => {
    dispatch(setPage(filters.page + 1));
  };

  const { data, isLoading } = useGetAllPrivacyRequestsQuery(cachedFilters);
  const { items: requests, total } = data || { items: [], total: 0 };
  return {
    ...filters,
    isLoading,
    requests,
    total,
    handleNextPage,
    handlePreviousPage,
  };
};

const RequestTable: React.FC<RequestTableProps> = () => {
  const { requests, total, page, size, handleNextPage, handlePreviousPage } =
    useRequestTable();
  const startingItem = (page - 1) * size + 1;
  const endingItem = Math.min(total, page * size);
  return (
    <>
      <Table size="sm">
        <Thead>
          <Tr>
            <Th pl={0}>Status</Th>
            <Th>Policy Name</Th>
            <Th>Subject Identity</Th>
            <Th>Time Received</Th>
            <Th>Reviewed By</Th>
            <Th>Request ID</Th>
            <Th />
          </Tr>
        </Thead>
        <Tbody>
          {requests.map((request) => (
            <RequestRow request={request} key={request.id} />
          ))}
        </Tbody>
      </Table>
      <Flex justifyContent="space-between" mt={6}>
        <Text fontSize="xs" color="gray.600">
          {total > 0 ? (
            <>
              Showing {Number.isNaN(startingItem) ? 0 : startingItem} to{' '}
              {Number.isNaN(endingItem) ? 0 : endingItem} of{' '}
              {Number.isNaN(total) ? 0 : total} results
            </>
          ) : (
            '0 results'
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

RequestTable.defaultProps = {
  requests: [],
};

export default RequestTable;
