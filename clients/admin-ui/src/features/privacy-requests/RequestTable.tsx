import { Checkbox, Flex, Table, Tbody, Th, Thead, Tr } from "@fidesui/react";
import React, { useCallback } from "react";

import { useAppDispatch, useAppSelector } from "~/app/hooks";

import PaginationFooter from "../common/PaginationFooter";
import {
  selectPrivacyRequestFilters,
  selectRetryRequests,
  setPage,
  setRetryRequests,
} from "./privacy-requests.slice";
import RequestRow from "./RequestRow";
import SortRequestButton from "./SortRequestButton";
import { PrivacyRequest, PrivacyRequestResponse } from "./types";

type RequestTableProps = {
  isFetching: boolean;
  data: PrivacyRequestResponse | undefined;
};

const RequestTable: React.FC<RequestTableProps> = ({
  isFetching = false,
  data = { items: [], total: 0 },
}) => {
  const dispatch = useAppDispatch();
  const filters = useAppSelector(selectPrivacyRequestFilters);
  const { checkAll, errorRequests } = useAppSelector(selectRetryRequests);
  const { items: requests, total } = data;

  const getErrorRequests = useCallback(
    () => requests.filter((r) => r.status === "error").map((r) => r.id),
    [requests]
  );

  const handleCheckChange = (id: string, checked: boolean) => {
    let list: string[];
    if (checked) {
      list = [...errorRequests, id];
    } else {
      list = errorRequests.filter((value) => value !== id);
    }
    dispatch(
      setRetryRequests({
        checkAll: checked && checkAll,
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

  return (
    <>
      <Table size="sm">
        <Thead>
          <Tr>
            <Th px={0}>
              <Checkbox
                aria-label="Select all"
                isChecked={checkAll}
                isDisabled={!requests.some((r) => r.status === "error")}
                onChange={handleCheckAll}
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
        page={filters.page}
        size={filters.size}
        total={total}
        handleNextPage={handleNextPage}
        handlePreviousPage={handlePreviousPage}
      />
    </>
  );
};

export default RequestTable;
