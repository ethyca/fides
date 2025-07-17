/* eslint-disable react/no-unstable-nested-components */
import { getCoreRowModel, useReactTable } from "@tanstack/react-table";
import dayjs, { Dayjs } from "dayjs";
import {
  AntButton as Button,
  AntDateRangePicker as DateRangePicker,
  AntDropdown as Dropdown,
  AntEmpty as Empty,
  AntFlex as Flex,
  AntPagination as Pagination,
  AntSelect as Select,
  Icons,
  useToast,
} from "fidesui";
import { stat } from "fs";
import { useParams, useSearchParams } from "next/navigation";
import { useRouter } from "next/router";
import React, { useEffect, useMemo, useReducer, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import PageHeader from "~/features/common/PageHeader";
import {
  FidesTableV2,
  PAGE_SIZES,
  PaginationBar,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { successToastParams } from "~/features/common/toast";
import { useGetAllHistoricalPrivacyPreferencesQuery } from "~/features/consent-reporting/consent-reporting.slice";
import ConsentLookupModal from "~/features/consent-reporting/ConsentLookupModal";
import ConsentReportDownloadModal from "~/features/consent-reporting/ConsentReportDownloadModal";
import ConsentTcfDetailModal from "~/features/consent-reporting/ConsentTcfDetailModal";
import useConsentReportingTableColumns from "~/features/consent-reporting/hooks/useConsentReportingTableColumns";
import { ConsentReportingSchema } from "~/types/api";

const getNextPage = (change: -1 | 1) => (previousPage: number) => {
  const nextPage = previousPage + change;
  if (nextPage > 0) {
    return nextPage;
  }
  return 1;
};

const pageReducer = (
  state: { page: number; pageSize: number },
  action:
    | { type: "NEXT" }
    | { type: "PREVIOUS" }
    | { type: "SET_PAGE_SIZE"; payload: number },
) => {
  switch (action.type) {
    case "NEXT":
      return {
        ...state,
        page: getNextPage(+1)(state.page),
      };
    case "PREVIOUS":
      return {
        ...state,
        page: getNextPage(-1)(state.page),
      };
    case "SET_PAGE_SIZE":
      return {
        ...state,
        page: 1,
        pageSize: action.payload,
      };
    default:
      return state;
  }
};

const Paginator = ({
  onPaginationChanged,
}: {
  onPaginationChanged: ({
    page,
    pageSize,
  }: {
    page: number;
    pageSize: number;
  }) => void;
}) => {
  const searchParams = useSearchParams();
  const intOrUndefined = (param: string) => {
    const value = searchParams?.get(param);
    if (value) {
      return parseInt(value, 10);
    }

    return undefined;
  };
  const initialPageSize = intOrUndefined("pageSize");
  const initialPage = intOrUndefined("page");
  // probably should use a reducer
  const [{ page, pageSize }, dispatch] = useReducer(pageReducer, {
    page: initialPage ?? 1,
    pageSize: initialPageSize ?? 25,
  });
  const previous = () => dispatch({ type: "PREVIOUS" });
  const next = () => dispatch({ type: "NEXT" });
  const setPageSize = (value: number) =>
    dispatch({ type: "SET_PAGE_SIZE", payload: value });
  const { push } = useRouter();

  useEffect(() => {
    const nextSearchParams: Record<string, string> = {};
    searchParams?.forEach((value, key) => {
      nextSearchParams[key] = value;
    });
    if (page > 1 || initialPage) {
      nextSearchParams.page = (page ?? 1).toString();
    }
    if (pageSize > 25 || initialPageSize) {
      nextSearchParams.pageSize = (pageSize ?? 25).toString();
    }
    push({
      query: new URLSearchParams(nextSearchParams).toString(),
    });

    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize]);

  useEffect(() => {
    onPaginationChanged({ page, pageSize });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page, pageSize]);

  return (
    <div style={{ display: "flex", columnGap: "10px", alignItems: "center" }}>
      <Button onClick={previous} disabled={page === 1}>
        Previous
      </Button>
      <span>{page}</span>
      <Button onClick={next}>Next</Button>
      <Select
        style={{ width: "auto" }}
        value={pageSize}
        onChange={setPageSize}
        options={[
          { label: 25, value: 25 },
          { label: 50, value: 50 },
          { label: 100, value: 100 },
        ]}
        labelRender={(option) => {
          return <span>{option.label} / page</span>;
        }}
      />
    </div>
  );
};

export default ConsentReportingPage;
