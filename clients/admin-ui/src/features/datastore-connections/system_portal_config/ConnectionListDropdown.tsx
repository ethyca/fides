import { debounce } from "common/utils";
import {
  AntButton as Button,
  ArrowDownLineIcon,
  Box,
  Flex,
  Input,
  InputGroup,
  InputLeftElement,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  SearchLineIcon,
  Text,
  Tooltip,
} from "fidesui";
import { useCallback, useMemo, useRef, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  selectConnectionTypeFilters,
  useGetAllConnectionTypesQuery,
} from "~/features/connection-type";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
} from "~/types/api";

type ItemOption = {
  /**
   * Specifies the value to be sent
   */
  value: ConnectionSystemTypeMap;
  /**
   * Specifies that an option should be disabled
   */
  isDisabled?: boolean;
  /**
   * Specifies a toolTip should be dislayed when the user hovers over an option
   */
  toolTip?: string;
};

type SelectDropdownProps = {
  /**
   * List of key/value pair items
   */
  list: Map<string, ItemOption>;
  /**
   * Parent callback event handler invoked when selected value has changed
   */
  onChange: (value: ConnectionSystemTypeMap | undefined) => void;
  /**
   * Placeholder
   */
  label: string;
  /**
   * Display the Clear button. Default value is true.
   */
  hasClear?: boolean;
  /**
   * Default value marked for selection
   */
  selectedValue?: ConnectionSystemTypeMap;
  /**
   * Disable the control
   */
  disabled?: boolean;
};

type UseConnectionListDropDown = {
  connectionConfig?: ConnectionConfigurationResponse | null;
};

export const useConnectionListDropDown = ({
  connectionConfig,
}: UseConnectionListDropDown) => {
  const filters = useAppSelector(selectConnectionTypeFilters);
  const { data } = useGetAllConnectionTypesQuery(filters);

  const connectionOptions = useMemo(() => data?.items || [], [data]);

  const [selectedValue, setSelectedValue] = useState<ConnectionSystemTypeMap>();

  const sortedItems = useMemo(
    () =>
      [...connectionOptions].sort((a, b) =>
        a.human_readable > b.human_readable ? 1 : -1,
      ),
    [connectionOptions],
  );

  const dropDownOptions = useMemo(() => {
    const options = new Map<string, ItemOption>();
    sortedItems?.map((i) =>
      options.set(i.human_readable, {
        value: i,
      }),
    );
    return options;
  }, [sortedItems]);

  const systemType = useMemo(
    () =>
      // this needs to factor in the selected value as well
      connectionOptions.find(
        (ct) =>
          ct.identifier === connectionConfig?.connection_type ||
          (connectionConfig?.saas_config &&
            ct.identifier === connectionConfig?.saas_config.type),
      )?.type || "ethyca",
    [connectionConfig, connectionOptions],
  );

  useMemo(() => {
    const initialSelectedValue = connectionOptions.find(
      (ct) =>
        (connectionConfig?.saas_config &&
          ct.identifier === connectionConfig?.saas_config.type) ||
        ct.identifier === connectionConfig?.connection_type,
    );
    if (initialSelectedValue) {
      setSelectedValue(initialSelectedValue);
    }
  }, [connectionConfig, connectionOptions]);

  return { dropDownOptions, selectedValue, setSelectedValue, systemType };
};

const ConnectionListDropdown = ({
  disabled,
  hasClear = true,
  label,
  list,
  onChange,
  selectedValue,
}: SelectDropdownProps) => {
  const inputRef = useRef<HTMLInputElement>(null);

  // Hooks
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");

  // Listeners
  const handleClose = () => {
    setIsOpen(false);
  };
  const handleClear = () => {
    onChange(undefined);
    setSearchTerm("");
    handleClose();
  };
  const handleOpen = () => {
    setIsOpen(true);
  };

  const selectedText = [...list].find(
    ([, option]) => option.value.identifier === selectedValue?.identifier,
  )?.[0];

  const handleSearchChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      if (event.target.value.length === 0 || event.target.value.length > 1) {
        setSearchTerm(event.target.value);
        setTimeout(() => inputRef.current?.focus(), 0);
      }
    },
    [],
  );

  const debounceHandleSearchChange = useMemo(
    () => debounce(handleSearchChange, 100),
    [handleSearchChange],
  );

  const filteredListItems = useMemo(
    () =>
      [...list].filter((l) =>
        l[0].toLowerCase().includes(searchTerm.toLowerCase()),
      ),
    [list, searchTerm],
  );

  return (
    <Menu
      isLazy
      onClose={handleClose}
      onOpen={handleOpen}
      strategy="fixed"
      matchWidth
    >
      <MenuButton
        aria-label={selectedText ?? label}
        as={Button}
        color={selectedText ? "complimentary.500" : undefined}
        disabled={disabled}
        icon={<ArrowDownLineIcon />}
        iconPosition="end"
        className="!bg-transparent text-left hover:bg-transparent active:bg-transparent"
        data-testid="select-dropdown-btn"
        width="272px"
      >
        <Text noOfLines={1} style={{ wordBreak: "break-all" }}>
          {selectedText ?? label}
        </Text>
      </MenuButton>
      {isOpen ? (
        <MenuList
          id="MENU_LIST"
          lineHeight="1rem"
          p="0"
          maxHeight="400px"
          overflow="hidden"
          data-testid="select-dropdown-list"
          width="272px"
        >
          <Box px="8px" mt={2}>
            <InputGroup size="sm">
              <InputLeftElement pointerEvents="none">
                <SearchLineIcon color="gray.300" h="17px" w="17px" />
              </InputLeftElement>
              <Input
                data-testid="input-search-integrations"
                ref={inputRef}
                autoComplete="off"
                autoFocus
                borderRadius="md"
                name="search"
                onChange={debounceHandleSearchChange}
                placeholder="Search integrations"
                size="sm"
                type="search"
              />
            </InputGroup>
          </Box>
          {hasClear && (
            <Flex
              borderBottom="1px"
              borderColor="gray.200"
              cursor="auto"
              p="8px"
            >
              <Button onClick={handleClear} size="small">
                Clear
              </Button>
            </Flex>
          )}
          {/* MenuItems are not rendered unless Menu is open */}
          <Box overflowY="auto" maxHeight="272px">
            {filteredListItems.map(([key, option]) => (
              <Tooltip
                aria-label={option.toolTip}
                hasArrow
                label={option.toolTip}
                key={key}
                placement="auto-start"
                openDelay={500}
                shouldWrapChildren
              >
                <MenuItem
                  color={
                    selectedValue === option.value
                      ? "complimentary.500"
                      : undefined
                  }
                  isDisabled={option.isDisabled}
                  onClick={() => onChange(option.value)}
                  paddingTop="10px"
                  paddingRight="8.5px"
                  paddingBottom="10px"
                  paddingLeft="8.5px"
                  _focus={{
                    bg: "gray.100",
                  }}
                >
                  <ConnectionTypeLogo data={option.value} />
                  <Text
                    ml={2}
                    fontSize="0.75rem"
                    noOfLines={1}
                    wordBreak="break-all"
                  >
                    {key}
                  </Text>
                </MenuItem>
              </Tooltip>
            ))}
          </Box>
        </MenuList>
      ) : null}
    </Menu>
  );
};

export default ConnectionListDropdown;
