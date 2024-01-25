import {
  Badge,
  Box,
  Button,
  ButtonGroup,
  Checkbox,
  Flex,
  ModalFooter,
  ModalHeader,
  Text,
} from "@fidesui/react";
import { ReactNode } from "react";

export const Header = ({ title }: { title: string }) => (
  <ModalHeader
    fontSize="lg"
    fontWeight="semibold"
    pt={5}
    paddingInline={6}
    pb={5}
    backgroundColor="gray.50"
    borderTopRadius="md"
    borderBottom="1px solid"
    borderColor="gray.200"
  >
    {title}
  </ModalHeader>
);

export const HeaderCheckboxRow = ({
  title,
  allSelected,
  numSelected,
  onToggleAll,
  children,
}: {
  title: string;
  allSelected: boolean;
  numSelected: number;
  onToggleAll: () => void;
  children?: ReactNode;
}) => (
  <Flex justifyContent="space-between" mb={4}>
    <Box>
      <Checkbox
        colorScheme="complimentary"
        size="md"
        isChecked={allSelected}
        isIndeterminate={!allSelected && numSelected > 0}
        onChange={onToggleAll}
        mr={3}
        data-testid="select-all"
      >
        <Text fontWeight="semibold" fontSize="md">
          {title}
        </Text>
      </Checkbox>
      <Badge
        colorScheme="purple"
        variant="solid"
        width="fit-content"
        data-testid="num-selected-badge"
      >
        {numSelected} selected
      </Badge>
    </Box>
    {children}
  </Flex>
);

export const Footer = ({
  onApply,
  onClose,
}: {
  onApply: () => void;
  onClose: () => void;
}) => (
  <ModalFooter justifyContent="center">
    <ButtonGroup
      size="sm"
      display="flex"
      justifyContent="space-between"
      width="100%"
    >
      <Button
        data-testid="cancel-btn"
        flexGrow={1}
        variant="outline"
        mr={3}
        onClick={onClose}
      >
        Cancel
      </Button>
      <Button
        flexGrow={1}
        colorScheme="primary"
        onClick={onApply}
        data-testid="apply-btn"
      >
        Apply
      </Button>
    </ButtonGroup>
  </ModalFooter>
);
