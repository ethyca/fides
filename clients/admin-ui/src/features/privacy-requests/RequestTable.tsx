import { Checkbox, Flex, Table, Tbody, Th, Thead, Tr } from "@fidesui/react";
import { debounce } from "common/utils";
import React, { useCallback, useEffect, useRef, useState } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import PaginationFooter from "../common/PaginationFooter";
import {
  selectPrivacyRequestFilters,
  selectRetryRequests,
  setPage,
  setRetryRequests,
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
  const updateCachedFilters = useRef(
    debounce(
      (updatedFilters: React.SetStateAction<PrivacyRequestParams>) =>
        setCachedFilters(updatedFilters),
      250
    )
  );

  const { checkAll, errorRequests } = useAppSelector(selectRetryRequests);
  const { data, isFetching } = useGetAllPrivacyRequestsQuery(cachedFilters);
  const { items: requests, total } = data || { items: [], total: 0 };

  const getErrorRequests = useCallback(
    () => requests.filter((r) => r.status === "error").map((r) => r.id),
    [requests]
  );

  const handleCheckChange = (id: string, checked: boolean) => {
    let list: string[];
    if (checked) {
      list = [...errorRequests, id];
    } else {
      errorRequests.filter((value) => value !== id);
      list = [...errorRequests.filter((value) => value !== id)];
    }
    dispatch(
      setRetryRequests({
        checkAll: !!(checked && checkAll),
        errorRequests: list,
      })
    );
  };

  const handlePreviousPage = () => {
    dispatch(setPage(filters.page - 1));
  };

  const handleNextPage = () => {
    dispatch(setPage(filters.page + 1));
  };

  const handleCheckAll = () => {
    const value = !checkAll;
    dispatch(
      setRetryRequests({
        checkAll: value,
        errorRequests: value ? getErrorRequests() : [],
      })
    );
  };

  useEffect(() => {
    updateCachedFilters.current(filters);
    if (isFetching && filters.status?.includes("error")) {
      dispatch(setRetryRequests({ checkAll: false, errorRequests: [] }));
    }
  }, [dispatch, filters, isFetching]);

  return {
    ...filters,
    checkAll,
    errorRequests,
    handleCheckChange,
    handleNextPage,
    handlePreviousPage,
    handleCheckAll,
    isFetching,
    requests,
    total,
  };
};

const RequestTable: React.FC<RequestTableProps> = () => {
  const {
    checkAll,
    errorRequests,
    handleCheckChange,
    handleNextPage,
    handlePreviousPage,
    handleCheckAll,
    isFetching,
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
                isChecked={checkAll}
                onChange={handleCheckAll}
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
