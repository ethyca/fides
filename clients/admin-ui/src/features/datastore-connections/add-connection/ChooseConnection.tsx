import {
  Box,
  Button,
  Center,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  SearchLineIcon,
  Spinner,
} from "@fidesui/react";
import { debounce } from "common/utils";
import {
  selectConnectionTypeFilters,
  selectConnectionTypeState,
  setSearch,
  useGetAllConnectionTypesQuery,
} from "connection-type/connection-type.slice";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { useDispatch } from "react-redux";
import { useAppSelector } from "~/app/hooks";
import ConnectorTemplateUploadModal from "../../connector-templates/ConnectorTemplateUploadModal";

import Breadcrumb from "./Breadcrumb";
import ConnectionTypeFilter from "./ConnectionTypeFilter";
import ConnectionTypeList from "./ConnectionTypeList";
import { STEPS } from "./constants";

const ChooseConnection: React.FC = () => {
  const dispatch = useDispatch();
  const mounted = useRef(false);
  const { step } = useAppSelector(selectConnectionTypeState);
  const filters = useAppSelector(selectConnectionTypeFilters);
  const { data, isFetching, isLoading, isSuccess } =
    useGetAllConnectionTypesQuery(filters);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleSearchChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.value.length === 0 || event.target.value.length > 1) {
        dispatch(setSearch(event.target.value));
      }
    },
    [dispatch]
  );

  const debounceHandleSearchChange = useMemo(
    () => debounce(handleSearchChange, 250),
    [handleSearchChange]
  );

  const sortedItems = useMemo(
    () =>
      data?.items &&
      [...data.items].sort((a, b) =>
        a.human_readable > b.human_readable ? 1 : -1
      ),
    [data]
  );

  const handleUploadButtonClick = () => {
    setIsModalOpen(true);
  };

  useEffect(() => {
    mounted.current = true;
    return () => {
      dispatch(setSearch(""));
      mounted.current = false;
    };
  }, [dispatch]);

  return (
    <>
      <Breadcrumb steps={[STEPS[0], STEPS[1]]} />
      <Flex minWidth="fit-content">
        <Box
          color="gray.700"
          fontSize="14px"
          maxHeight="80px"
          maxWidth="474px"
          mb="24px"
        >
          {step.description}
        </Box>
      </Flex>
      <Flex alignItems="center" gap="4" mb="24px" minWidth="fit-content">
        <ConnectionTypeFilter />
        <InputGroup size="sm">
          <InputLeftElement pointerEvents="none">
            <SearchLineIcon color="gray.300" h="17px" w="17px" />
          </InputLeftElement>
          <Input
            autoComplete="off"
            autoFocus
            borderRadius="md"
            name="search"
            onChange={debounceHandleSearchChange}
            placeholder="Search Integrations"
            size="sm"
            type="search"
          />
        </InputGroup>
        <Button
          colorScheme="primary"
          type="submit"
          width="20%"
          data-testid="upload-btn"
          size="sm"
          onClick={handleUploadButtonClick}
        >
          Upload Connector
        </Button>
      </Flex>
      <ConnectorTemplateUploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess && sortedItems ? (
        <ConnectionTypeList items={sortedItems} />
      ) : null}
    </>
  );
};

export default ChooseConnection;
