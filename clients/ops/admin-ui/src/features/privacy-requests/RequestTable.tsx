import { Flex, Table, Tbody, Th, Thead, Tr } from "@fidesui/react";
import { debounce } from "common/utils";
import React, { useEffect, useRef, useState } from "react";
import { useDispatch, useSelector } from "react-redux";

import PaginationFooter from "../common/PaginationFooter";
import {
  selectPrivacyRequestFilters,
  setPage,
  useGetAllPrivacyRequestsQuery,
} from "./privacy-requests.slice";
import RequestRow from "./RequestRow";
import SortRequestButton from "./SortRequestButton";
import { PrivacyRequest, PrivacyRequestParams } from "./types";

interface RequestTableProps {
  requests?: PrivacyRequest[];
}

const useRequestTable = () => {
  const dispatch = useDispatch();
  const filters = useSelector(selectPrivacyRequestFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const updateCachedFilters = useRef(
    debounce(
      (updatedFilters: React.SetStateAction<PrivacyRequestParams>) =>
        setCachedFilters(updatedFilters),
      250
    )
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

  const { data, isLoading, isFetching } =
    useGetAllPrivacyRequestsQuery(cachedFilters);
  const { items: requests, total } = data || { items: [], total: 0 };
  return {
    ...filters,
    isLoading,
    isFetching,
    requests,
    total,
    handleNextPage,
    handlePreviousPage,
  };
};

const RequestTable: React.FC<RequestTableProps> = () => {
  const {
    requests,
    total,
    page,
    size,
    handleNextPage,
    handlePreviousPage,
    isFetching,
  } = useRequestTable();

  return (
    <>
      <Table size="sm">
        <Thead>
          <Tr>
            <Th pl={0}>Status</Th>
            <Th>
              <Flex alignItems="center">
                Days Left{" "}
                <SortRequestButton
                  sortField="due_date"
                  isLoading={isFetching}
                />
              </Flex>
            </Th>
            <Th>Request Type</Th>
            <Th>Subject Identity</Th>
            <Th>Time Received</Th>
            <Th>Reviewed By</Th>
            <Th>Request ID</Th>
            <Th />
          </Tr>
        </Thead>
        <Tbody>
          {requests.map((request: any) => (
            <RequestRow request={request} key={request.id} />
          ))}
        </Tbody>
      </Table>
      <PaginationFooter
        page={page}
        size={size}
        total={total}
        handleNextPage={handleNextPage}
        handlePreviousPage={handlePreviousPage}
      />
    </>
  );
};

RequestTable.defaultProps = {
  requests: [],
};

export default RequestTable;
