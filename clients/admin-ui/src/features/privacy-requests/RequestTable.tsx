import { Checkbox, Flex, Table, Tbody, Th, Thead, Tr } from "@fidesui/react";
import { debounce } from "common/utils";
import React, { useCallback, useEffect, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import PaginationFooter from "../common/PaginationFooter";
import {
  selectErrorRequests,
  selectPrivacyRequestFilters,
  setErrorRequests,
  setPage,
  useGetAllPrivacyRequestsQuery,
} from "./privacy-requests.slice";
import RequestRow from "./RequestRow";
import SortRequestButton from "./SortRequestButton";
import { PrivacyRequest, PrivacyRequestParams } from "./types";

type RequestTableProps = {
  requests?: PrivacyRequest[];
};

const useRequestTable = () => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector(selectPrivacyRequestFilters);
  const [cachedFilters, setCachedFilters] = useState(filters);
  const [isSelectAll, setIsSelectAll] = useState(false);
  const updateCachedFilters = useRef(
    debounce(
      (updatedFilters: React.SetStateAction<PrivacyRequestParams>) =>
        setCachedFilters(updatedFilters),
      250
    )
  );

  const errorRequests = useAppSelector(selectErrorRequests);
  const { data, isFetching } = useGetAllPrivacyRequestsQuery(cachedFilters);
  const { items: requests, total } = data || { items: [], total: 0 };

  const getErrorRequests = useCallback(
    () => requests.filter((r) => r.status === "error").map((r) => r.id),
    [requests]
  );

  const handleCheckChange = (id: string, checked: boolean) => {
    if (!checked && isSelectAll) {
      setIsSelectAll(false);
    }
    let list: string[];
    if (checked) {
      list = [...errorRequests, id];
    } else {
      list = [...errorRequests];
      const index = list.findIndex((value) => value === id);
      list.splice(index, 1);
    }
    dispatch(setErrorRequests(list));
  };

  const handlePreviousPage = () => {
    dispatch(setPage(filters.page - 1));
  };

  const handleNextPage = () => {
    dispatch(setPage(filters.page + 1));
  };

  const handleSelectAll = () => {
    const value = !isSelectAll;
    setIsSelectAll(value);
    dispatch(setErrorRequests(value ? getErrorRequests() : []));
  };

  useEffect(() => {
    updateCachedFilters.current(filters);
  }, [filters]);

  return {
    ...filters,
    errorRequests,
    handleCheckChange,
    handleNextPage,
    handlePreviousPage,
    handleSelectAll,
    isFetching,
    isSelectAll,
    requests,
    total,
  };
};

const RequestTable: React.FC<RequestTableProps> = () => {
  const {
    errorRequests,
    handleCheckChange,
    handleNextPage,
    handlePreviousPage,
    handleSelectAll,
    isFetching,
    isSelectAll,
    page,
    requests,
    size,
    total,
  } = useRequestTable();

  return (
    <>
      <Table size="sm">
        <Thead>
          <Tr>
            <Th px={0}>
              <Checkbox
                aria-label="Select all"
                isChecked={isSelectAll}
                onChange={handleSelectAll}
                pointerEvents={
                  requests.findIndex((r) => r.status === "error") !== -1
                    ? "auto"
                    : "none"
                }
              />
            </Th>
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
          {requests.map((request: PrivacyRequest) => (
            <RequestRow
              key={request.id}
              isChecked={errorRequests.includes(request.id)}
              onCheckChange={handleCheckChange}
              request={request}
            />
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
