import {
  Button,
  Flex,
  Input,
  InputGroup,
  InputLeftAddon,
  InputLeftElement,
  Stack,
  Text,
  useToast,
} from "@fidesui/react";
import MultiSelectDropdown from "common/dropdown/MultiSelectDropdown";
import React, { useCallback, useMemo } from "react";
import { useDispatch, useSelector } from "react-redux";

import { selectToken } from "../auth";
import {
  CloseSolidIcon,
  DownloadSolidIcon,
  SearchLineIcon,
} from "../common/Icon";
import PIIToggle from "../common/PIIToggle";
import {
  clearAllFilters,
  requestCSVDownload,
  selectPrivacyRequestFilters,
  setRequestFrom,
  setRequestId,
  setRequestStatus,
  setRequestTo,
} from "../privacy-requests/privacy-requests.slice";
import { PrivacyRequestStatus } from "../privacy-requests/types";
import { SubjectRequestStatusMap } from "./constants";

const useRequestFilters = () => {
  const filters = useSelector(selectPrivacyRequestFilters);
  const token = useSelector(selectToken);
  const dispatch = useDispatch();
  const toast = useToast();

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestId(event.target.value));
  const handleStatusChange = useCallback(
    (values: string[]) => {
      const list: PrivacyRequestStatus[] = [];
      values.forEach((v) => {
        SubjectRequestStatusMap.forEach((value, key) => {
          if (key === v) {
            list.push(value as PrivacyRequestStatus);
          }
        });
      });
      dispatch(setRequestStatus(list));
    },
    [dispatch]
  );
  const handleFromChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestFrom(event?.target.value));
  const handleToChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestTo(event?.target.value));
  const handleClearAllFilters = () => dispatch(clearAllFilters());
  const handleDownloadClick = async () => {
    let message;
    try {
      await requestCSVDownload({ ...filters, token });
    } catch (error) {
      if (error instanceof Error) {
        message = error.message;
      } else {
        message = "Unknown error occurred";
      }
    }
    if (message) {
      toast({
        description: `${message}`,
        duration: 5000,
        status: "error",
      });
    }
  };
  const loadStatusList = (values: string[]): Map<string, boolean> => {
    const list = new Map<string, boolean>();
    SubjectRequestStatusMap.forEach((value, key) => {
      let result = false;
      if (values.includes(value)) {
        result = true;
      }
      list.set(key, result);
    });
    return list;
  };

  // Load the status list
  const statusList = useMemo(
    () => loadStatusList(filters.status || []),
    [filters.status]
  );

  // Filter the selected status list
  const selectedStatusList = new Map(
    [...statusList].filter(([, v]) => v === true)
  );

  return {
    handleSearchChange,
    handleStatusChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    handleDownloadClick,
    loadStatusList,
    ...filters,
    selectedStatusList,
    statusList,
  };
};

const RequestFilters: React.FC = () => {
  const {
    handleSearchChange,
    handleStatusChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    handleDownloadClick,
    id,
    from,
    selectedStatusList,
    statusList,
    to,
  } = useRequestFilters();

  return (
    <Stack direction="row" spacing={4} mb={6}>
      <MultiSelectDropdown
        label="Select Status"
        list={statusList}
        selectedList={selectedStatusList}
        width="144px"
        onChange={handleStatusChange}
        tooltipPlacement="top"
      />
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
        <Input
          autoComplete="off"
          autoFocus
          type="search"
          minWidth={200}
          placeholder="Search"
          size="sm"
          borderRadius="md"
          value={id}
          name="search"
          onChange={handleSearchChange}
        />
      </InputGroup>
      <InputGroup size="sm">
        <InputLeftAddon borderRadius="md">From</InputLeftAddon>
        <Input
          type="date"
          name="From"
          value={from}
          max={to || undefined}
          onChange={handleFromChange}
          borderRadius="md"
        />
      </InputGroup>
      <InputGroup size="sm">
        <InputLeftAddon borderRadius="md">To</InputLeftAddon>
        <Input
          type="date"
          borderRadius="md"
          name="To"
          value={to}
          min={from || undefined}
          onChange={handleToChange}
        />
      </InputGroup>
      <Flex flexShrink={0} alignItems="center">
        <Text fontSize="xs" mr={2} size="sm">
          Reveal PII
        </Text>
        <PIIToggle />
      </Flex>
      <Button
        variant="ghost"
        flexShrink={0}
        rightIcon={<DownloadSolidIcon />}
        size="sm"
        onClick={handleDownloadClick}
      >
        Download
      </Button>
      <Button
        variant="ghost"
        flexShrink={0}
        rightIcon={<CloseSolidIcon />}
        size="sm"
        onClick={handleClearAllFilters}
      >
        Clear all filters
      </Button>
    </Stack>
  );
};

export default RequestFilters;
