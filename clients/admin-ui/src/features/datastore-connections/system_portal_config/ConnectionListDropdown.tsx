import {
  ArrowDownLineIcon,
  Button,
  ButtonProps,
  Flex,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Text,
  Tooltip,
  Box,
} from "@fidesui/react";
import { useState, useMemo } from "react";
import { useAppSelector } from "~/app/hooks";
import {
  selectConnectionTypeFilters,
  selectConnectionTypes,
  setSearch,
  useGetAllConnectionTypesQuery,
} from "~/features/connection-type";
import {
  ConnectionConfigurationResponse,
  ConnectionSystemTypeMap,
} from "~/types/api";
import ConnectionTypeLogo from "~/features/datastore-connections/ConnectionTypeLogo";

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
   * Sort the list items before rendering
   */
  enableSorting?: boolean;
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
  /**
   * Menu button props
   */
  menuButtonProps?: ButtonProps;
};

type UseConnectionListDropDown = {
  connectionConfig?: ConnectionConfigurationResponse;
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
        a.human_readable > b.human_readable ? 1 : -1
      ),
    [connectionOptions]
  );

  const dropDownOptions = useMemo(() => {
    const options = new Map<string, ItemOption>();
    sortedItems?.map((i) => {
      options.set(i.human_readable, {
        value: i,
      });
    });
    return options;
  }, [sortedItems]);

  const systemType = useMemo(() => {
    //this needs to factor in the selected value as well
    return (
      connectionOptions.find(
        (ct) =>
          ct.identifier === connectionConfig?.connection_type ||
          (connectionConfig?.saas_config &&
            ct.identifier === connectionConfig?.saas_config.type)
      )?.type || "ethyca"
    );
  }, [connectionConfig, connectionOptions]);

  useMemo(() => {
    const initialSelectedValue = connectionOptions.find(
      (c) => c.identifier === connectionConfig?.connection_type
    );
    if (initialSelectedValue) {
      setSelectedValue(initialSelectedValue);
    }
  }, [connectionConfig, connectionOptions]);

  return { dropDownOptions, selectedValue, setSelectedValue, systemType };
};

const ConnectionListDropdown: React.FC<SelectDropdownProps> = ({
  disabled = false,
  enableSorting = true,
  hasClear = true,
  label,
  list,
  menuButtonProps,
  onChange,
  selectedValue,
}) => {
  // Hooks
  const [isOpen, setIsOpen] = useState(false);

  // Listeners
  const handleClose = () => {
    setIsOpen(false);
  };
  const handleClear = () => {
    onChange(undefined);
    handleClose();
  };
  const handleOpen = () => {
    setIsOpen(true);
  };

  const selectedText = [...list].find(
    ([, option]) => option.value.identifier === selectedValue?.identifier
  )?.[0];

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
        fontWeight="normal"
        rightIcon={<ArrowDownLineIcon />}
        size="sm"
        variant="outline"
        _active={{
          bg: "none",
        }}
        _hover={{
          bg: "none",
        }}
        {...menuButtonProps}
        data-testid="select-dropdown-btn"
        width="300px"
        textAlign="left"
      >
        <Text isTruncated>{selectedText ?? label}</Text>
      </MenuButton>
      {isOpen ? (
        <MenuList
          id="MENU_LIST"
          lineHeight="1rem"
          p="0"
          maxHeight="400px"
          overflow="hidden"
          data-testid="select-dropdown-list"
          width="300px"
        >
          {hasClear && (
            <Flex
              borderBottom="1px"
              borderColor="gray.200"
              cursor="auto"
              p="8px"
            >
              <Button onClick={handleClear} size="xs" variant="outline">
                Clear
              </Button>
            </Flex>
          )}
          {/* MenuItems are not rendered unless Menu is open */}
          <Box overflowY="auto" maxHeight="300px">
            {(enableSorting ? [...list].sort() : [...list]).map(
              ([key, option]) => (
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
                    <Text ml={2} fontSize="0.75rem" isTruncated>
                      {key}
                    </Text>
                  </MenuItem>
                </Tooltip>
              )
            )}
          </Box>
        </MenuList>
      ) : null}
    </Menu>
  );
};

export default ConnectionListDropdown;
