import {
  Input,
  InputGroup,
  InputLeftElement,
  Select,
  Stack,
  useToast,
} from "@fidesui/react";
import React from "react";
import { useDispatch, useSelector } from "react-redux";

import { selectToken } from "../auth";
import { SearchLineIcon } from "../common/Icon";
import { capitalize } from "../common/utils";
import {
  clearAllFilters,
  requestCSVDownload,
  selectPrivacyRequestFilters,
  setRequestFrom,
  setRequestId,
  setRequestStatus,
  setRequestTo,
} from "../privacy-requests";
import { PrivacyRequestStatus } from "../privacy-requests/types";
import { ConnectionType, SystemType, TestingStatus } from "./types";

const useConstantFilters = () => {
  const filters = useSelector(selectPrivacyRequestFilters);
  const token = useSelector(selectToken);
  const dispatch = useDispatch();
  const toast = useToast();
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) =>
    dispatch(setRequestId(event.target.value));
  const handleStatusChange = (event: React.ChangeEvent<HTMLSelectElement>) =>
    dispatch(setRequestStatus(event.target.value as PrivacyRequestStatus));
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

  return {
    handleSearchChange,
    handleStatusChange,
    handleFromChange,
    handleToChange,
    handleClearAllFilters,
    handleDownloadClick,
    ...filters,
  };
};

const DataStoreTypeOption: React.FC<{ status: ConnectionType }> = ({
  status,
}) => <option value={status}>{capitalize(status)}</option>;

const SystemTypeOption: React.FC<{ status: SystemType }> = ({ status }) => (
  <option value={status}>{capitalize(status)}</option>
);

const TestingStatusOption: React.FC<{ status: TestingStatus }> = ({
  status,
}) => <option value={status}>{capitalize(status)}</option>;

const ConnectionFilters: React.FC = () => {
  const { status, handleSearchChange, handleStatusChange, id } =
    useConstantFilters();
  return (
    <Stack direction="row" spacing={4} mb={6}>
      <InputGroup size="sm">
        <InputLeftElement pointerEvents="none">
          <SearchLineIcon color="gray.300" w="17px" h="17px" />
        </InputLeftElement>
        <Input
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
      <Select
        placeholder="Datastore Type"
        size="sm"
        minWidth="144px"
        value={status || ""}
        onChange={handleStatusChange}
        borderRadius="md"
      >
        <DataStoreTypeOption status={ConnectionType.POSTGRES} />
        <DataStoreTypeOption status={ConnectionType.MONGODB} />
        <DataStoreTypeOption status={ConnectionType.MYSQL} />
        <DataStoreTypeOption status={ConnectionType.HTTPS} />
        <DataStoreTypeOption status={ConnectionType.REDSHIFT} />
        <DataStoreTypeOption status={ConnectionType.SNOWFLAKE} />
        <DataStoreTypeOption status={ConnectionType.MSSQL} />
        <DataStoreTypeOption status={ConnectionType.MARIADB} />
        <DataStoreTypeOption status={ConnectionType.BIGQUERY} />
        <DataStoreTypeOption status={ConnectionType.MANUAL} />
      </Select>
      <Select
        placeholder="System Type"
        size="sm"
        minWidth="144px"
        value={status || ""}
        onChange={handleStatusChange}
        borderRadius="md"
      >
        <SystemTypeOption status={SystemType.SAAS} />
        <SystemTypeOption status={SystemType.DATABASE} />
        <SystemTypeOption status={SystemType.MANUAL} />
      </Select>
      <Select
        placeholder="Testing Status"
        size="sm"
        minWidth="144px"
        value={status || ""}
        onChange={handleStatusChange}
        borderRadius="md"
      >
        <TestingStatusOption status={TestingStatus.PASSED} />
        <TestingStatusOption status={TestingStatus.FAILED} />
        <TestingStatusOption status={TestingStatus.UNTESTED} />
      </Select>
      <Select
        placeholder="Status"
        size="sm"
        minWidth="144px"
        value={status || ""}
        onChange={handleStatusChange}
        borderRadius="md"
      >
        <option value="false">Enabled</option>
        <option value="true">Disabled</option>
      </Select>
    </Stack>
  );
};

export default ConnectionFilters;
