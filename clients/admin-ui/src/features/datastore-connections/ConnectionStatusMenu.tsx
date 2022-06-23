import {
  Box,
  Button,
  Checkbox,
  Flex,
  IconButton,
  Spacer,
  Text,
} from "@fidesui/react";
import React, { useCallback, useState } from "react";
import { useDispatch } from "react-redux";

import { useOutsideClick } from "../common/hooks";
import { ArrowDownLineIcon } from "../common/Icon";
import { capitalize } from "../common/utils";
import { setConnectionType } from "./datastore-connection.slice";
import { ConnectionType } from "./types";

type ConnectionCheckboxProps = {
  datastore: string;
  checked: boolean;
  onChecked: () => void;
};

const ConnectionCheckbox: React.FC<ConnectionCheckboxProps> = ({
  datastore,
  checked,
  onChecked,
}) => (
  <Flex padding="8px" flexDirection="column" _hover={{ bg: "gray.100" }}>
    <Flex>
      <Checkbox
        colorScheme="purple"
        isChecked={checked}
        onChange={() => {
          onChecked();
        }}
      />
      <Text
        marginLeft="8px"
        fontSize="xs"
        fontWeight="500"
        color="gray.700"
        lineHeight="16px"
      >
        {capitalize(datastore)}
      </Text>
    </Flex>
  </Flex>
);
type CheckBoxData = { type: ConnectionType; checked: boolean };

const initialCheckListState: CheckBoxData[] = [
  { type: ConnectionType.SAAS, checked: false },
  { type: ConnectionType.POSTGRES, checked: false },
  { type: ConnectionType.MONGODB, checked: false },
  { type: ConnectionType.MYSQL, checked: false },
  { type: ConnectionType.REDSHIFT, checked: false },
  { type: ConnectionType.SNOWFLAKE, checked: false },
  { type: ConnectionType.MSSQL, checked: false },
  { type: ConnectionType.MARIADB, checked: false },
  { type: ConnectionType.BIGQUERY, checked: false },
  { type: ConnectionType.MANUAL, checked: false },
  { type: ConnectionType.HTTPS, checked: false },
];

const useConnectionStatusMenu = () => {
  const disbatch = useDispatch();
  const [isOpen, setIsOpen] = useState<boolean>(false);
  const [checkboxStates, setCheckBoxStates] = useState<CheckBoxData[]>(
    initialCheckListState
  );

  const handleClick = useCallback(() => {
    if (isOpen) {
      setIsOpen(false);
    }
  }, [isOpen, setIsOpen]);

  const { ref } = useOutsideClick(handleClick);

  const updateCheckBoxStates = (data: CheckBoxData) => {
    const idx = checkboxStates.findIndex((d) => d.type === data.type);
    const newList = [...checkboxStates];
    newList[idx] = { type: data.type, checked: !data.checked };
    setCheckBoxStates(newList);
  };

  const resetCheckboxStates = () => {
    setCheckBoxStates([...initialCheckListState]);
  };

  const updateConnectionTypeFilter = () => {
    const connectionTypes = checkboxStates
      .filter((d) => d.checked)
      .map((d) => d.type);
    disbatch(setConnectionType(connectionTypes));
  };

  const toggleMenu = () => {
    setIsOpen(!isOpen);
  };
  const closeMenu = () => {
    setIsOpen(false);
  };
  return {
    isOpen,
    toggleMenu,
    closeMenu,
    checkboxStates,
    updateCheckBoxStates,
    resetCheckboxStates,
    updateConnectionTypeFilter,
    ref,
  };
};

const ConnectionStatusMenu: React.FC = () => {
  const {
    isOpen,
    toggleMenu,
    closeMenu,
    checkboxStates,
    updateCheckBoxStates,
    resetCheckboxStates,
    updateConnectionTypeFilter,
    ref,
  } = useConnectionStatusMenu();
  const checkboxes = checkboxStates.map((d) => (
    <ConnectionCheckbox
      key={d.type}
      datastore={d.type}
      checked={d.checked}
      onChecked={() => {
        updateCheckBoxStates(d);
      }}
    />
  ));

  const totalChecked = checkboxStates.filter((d) => d.checked).length;
  return (
    <Box width="100%" position="relative" ref={ref}>
      <Flex
        borderRadius="6px"
        border="1px"
        borderColor={isOpen ? "primary.600" : "gray.200"}
        height="32px"
        paddingRight="14px"
        paddingLeft="14px"
        alignItems="center"
      >
        <Text
          fontSize="14px"
          fontWeight="400"
          lineHeight="20px"
          color="gray.700"
        >
          Datastore Type
        </Text>
        {totalChecked ? (
          <Text
            paddingLeft="7px"
            fontSize="14px"
            fontWeight="400"
            lineHeight="20px"
            color="complimentary.500"
          >
            {totalChecked}
          </Text>
        ) : null}

        <Spacer />
        <IconButton
          variant="ghost"
          size="xs"
          aria-label="Datastore Type Dropdown"
          onClick={() => toggleMenu()}
          icon={<ArrowDownLineIcon />}
        />
      </Flex>
      {isOpen ? (
        <Flex
          marginTop="4px"
          backgroundColor="white"
          flexDirection="column"
          border="1px"
          width="100%"
          borderColor="gray.200"
          boxShadow="0px 1px 3px rgba(0, 0, 0, 0.1), 0px 1px 2px rgba(0, 0, 0, 0.06);"
          borderRadius="4px"
          position="absolute"
          zIndex={1}
        >
          <Flex borderBottom="1px" borderColor="gray.200" padding="8px">
            <Button
              size="xs"
              variant="outline"
              onClick={() => {
                resetCheckboxStates();
              }}
            >
              Clear
            </Button>
            <Spacer />
            <Button
              size="xs"
              backgroundColor="primary.800"
              color="white"
              onClick={() => {
                updateConnectionTypeFilter();
                closeMenu();
              }}
            >
              Done
            </Button>
          </Flex>
          {checkboxes}
        </Flex>
      ) : null}
    </Box>
  );
};

export default ConnectionStatusMenu;
