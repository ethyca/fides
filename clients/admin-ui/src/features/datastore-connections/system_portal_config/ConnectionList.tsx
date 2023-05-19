import {
  Center,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  SearchLineIcon,
  Select,
  Spinner,
} from "@fidesui/react";
import { debounce } from "common/utils";
import {
  selectConnectionTypeFilters,
  setSearch,
  useGetAllConnectionTypesQuery,
} from "connection-type/connection-type.slice";
import React, { useCallback, useMemo } from "react";
import { useDispatch } from "react-redux";

import { useAppSelector } from "~/app/hooks";

import ConnectionTypeFilter from "../add-connection/ConnectionTypeFilter";

// type ItemProps = {
//   data: ConnectionSystemTypeMap;
// };
// const ConnectinListItem = ({ data }: ItemProps) => (
//     <Box
//       boxShadow="base"
//       borderRadius="5px"
//       maxWidth="331px"
//       overflow="hidden"
//       _hover={{
//         boxShadow: "lg",
//         cursor: "pointer",
//       }}
//       data-testid={`${data.identifier}-item`}
//     >
//       <Flex alignItems="center" justifyContent="start" pl="24px" h="25px">
//         <ConnectionTypeLogo data={data} />
//         <Text
//           marginLeft="12px"
//           color="gray.700"
//           fontSize="sm"
//           fontStyle="normal"
//           fontWeight="600"
//         >
//           {data.human_readable}
//         </Text>
//       </Flex>
//     </Box>
//   );
//
type ListProps = {
  onChange: (e: React.ChangeEvent<HTMLSelectElement>) => void;
  // connectionConfig?: ConnectionConfigurationResponse;
};
const ConnectionList = ({ onChange }: ListProps) => {
  const dispatch = useDispatch();
  const filters = useAppSelector(selectConnectionTypeFilters);
  const { data, isFetching, isLoading, isSuccess } =
    useGetAllConnectionTypesQuery(filters);

  // const [selectedOption, setSelectedOption] = useState<string>();
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

  const dropDownOptions = useMemo(
    () =>
      sortedItems
        ? sortedItems.map((item) => ({
            label: item.human_readable,
            value: item,
          }))
        : [],
    [sortedItems]
  );

  // useMemo(() => {
  //   if (connectionConfig && sortedItems) {
  //     const c = sortedItems.find(
  //       (c) => c.identifier === connectionConfig.connection_type
  //     );
  //     onChange({
  //       target: {
  //         value: JSON.stringify(c),
  //       },
  //     } as React.ChangeEvent<HTMLSelectElement>);
  //     // setSelectedOption(JSON.stringify(c))
  //   }
  // }, [connectionConfig, sortedItems]);

  return (
    <>
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
      </Flex>
      {(isFetching || isLoading) && (
        <Center>
          <Spinner />
        </Center>
      )}
      {isSuccess && sortedItems ? (
        <Select
          onChange={(e) => {
            setSelectedOption(JSON.stringify(e.target.value));
            onChange(e);
          }}
        >
          {dropDownOptions.map((item) => (
            <option key={item.label} value={JSON.stringify(item.value)}>
              {item.label}
            </option>
          ))}
        </Select>
      ) : null}
    </>
  );
};

export default ConnectionList;
