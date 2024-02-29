import {
  ArrowDownIcon,
  ArrowUpIcon,
  Badge,
  Box,
  Checkbox,
  CheckboxProps,
  Flex,
  Switch,
  Text,
  useDisclosure,
  useToast,
  WarningIcon,
} from "@fidesui/react";
import { CellContext, HeaderContext } from "@tanstack/react-table";
import { ChangeEvent, FC, ReactNode } from "react";
import { CellProps } from "react-table";
import { getErrorMessage, isErrorResult } from "../../helpers";
import ConfirmationModal from "../../modals/ConfirmationModal";
import { errorToastParams } from "../../toast";
import { RTKResult } from "~/types/errors";

export const DefaultCell = ({
  value,
}: {
  value: string | undefined | number | boolean;
}) => (
  <Flex alignItems="center" height="100%">
    <Text
      fontSize="xs"
      lineHeight={4}
      fontWeight="normal"
      overflow="hidden"
      textOverflow="ellipsis"
    >
      {value !== null && value !== undefined ? value.toString() : value}
    </Text>
  </Flex>
);

const FidesBadge: FC = ({ children }) => (
  <Badge
    textTransform="none"
    fontWeight="400"
    fontSize="xs"
    lineHeight={4}
    color="gray.600"
    px={2}
    py={1}
  >
    {children}
  </Badge>
);

export const BadgeCell = ({
  value,
  suffix,
}: {
  value: string | number;
  suffix?: string;
}) => (
  <Flex alignItems="center" height="100%" mr="2">
    <FidesBadge>
      {value}
      {suffix ? ` ${suffix}` : null}
    </FidesBadge>
  </Flex>
);

export const GroupCountBadgeCell = ({
  value,
  suffix,
  isDisplayAll,
}: {
  value: string[] | string | undefined;
  suffix?: string;
  isDisplayAll?: boolean;
}) => {
  let badges = null;
  if (!value) {
    return <FidesBadge>0{suffix ? ` ${suffix}` : ""}</FidesBadge>;
  }
  if (Array.isArray(value)) {
    // If there's only one value, always display it
    if (value.length === 1) {
      badges = <FidesBadge>{value}</FidesBadge>;
    }
    // Expanded case, list every value as a badge
    else if (isDisplayAll && value.length > 0) {
      badges = value.map((d) => (
        <Box key={d} mr={2}>
          <FidesBadge>{d}</FidesBadge>
        </Box>
      ));
    }
    // Collapsed case, summarize the values in one badge
    else {
      badges = (
        <FidesBadge>
          {value.length}
          {suffix ? ` ${suffix}` : null}
        </FidesBadge>
      );
    }
  } else {
    badges = <FidesBadge>{value}</FidesBadge>;
  }

  return (
    <Flex alignItems="center" height="100%" mr="2" overflowX="hidden">
      {badges}
    </Flex>
  );
};

export const IndeterminateCheckboxCell = ({
  dataTestId,
  ...rest
}: CheckboxProps & { dataTestId?: string }) => (
  <Flex alignItems="center" justifyContent="center">
    <Checkbox
      data-testid={dataTestId || undefined}
      {...rest}
      colorScheme="purple"
    />
  </Flex>
);

type DefaultHeaderCellProps<T, V> = {
  value: V;
} & HeaderContext<T, V>;

export const DefaultHeaderCell = <T,>({
  value,
  column,
}: DefaultHeaderCellProps<
  T,
  string | number | string[] | undefined | boolean
>) => {
  let sortIcon: ReactNode = null;
  if (column.getIsSorted()) {
    sortIcon =
      column.getAutoSortDir() === "desc" ? (
        <ArrowDownIcon color="gray.500" />
      ) : (
        <ArrowUpIcon color="gray.500" />
      );
  }

  return (
    <Text
      _hover={{ backgroundColor: "gray.100" }}
      fontSize="xs"
      lineHeight={4}
      fontWeight="medium"
      pr={sortIcon ? 0 : 3.5}
      onClick={column.getToggleSortingHandler()}
    >
      {value}
      {sortIcon}
    </Text>
  );
};

type EnableCellProps<T extends object> = CellContext<T, boolean> & {
  value: boolean;
  onToggle: (data: boolean) => Promise<RTKResult>;
  title: string;
  message: string;
  /**
   * Disables the toggle. Can also pass a prop on `column`.
   * If either are true, then the toggle is disabled.
   */
  isDisabled?: boolean;
};

export const EnableCell = <T extends object>({
  value,
  column,
  onToggle,
  title,
  message,
  isDisabled,
}: EnableCellProps<T>) => {
  const modal = useDisclosure();
  const toast = useToast();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    const result = await onToggle(enable);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    }
  };

  const handleToggle = async (event: ChangeEvent<HTMLInputElement>) => {
    event.stopPropagation();
    const { checked } = event.target;
    if (checked) {
      await handlePatch({ enable: true });
    } else {
      modal.onOpen();
    }
  };

  return (
    <>
      <Switch
        colorScheme="complimentary"
        isChecked={!value}
        data-testid={`toggle-${column.Header}`}
        /**
         * It's difficult to use a custom column in react-table 7 since we'd have to modify
         * the declaration file. However, that modifies the type globally, so our datamap table
         * would also have issues. Ignoring the type for now, but should potentially revisit
         * if we update to react-table 8
         * https://github.com/DefinitelyTyped/DefinitelyTyped/discussions/59837
         */
        // @ts-ignore
        disabled={isDisabled || column.disabled}
        onChange={handleToggle}
      />
      <ConfirmationModal
        isOpen={modal.isOpen}
        onClose={modal.onClose}
        onConfirm={() => {
          handlePatch({ enable: false });
          modal.onClose();
        }}
        title={title}
        message={<Text color="gray.500">{message}</Text>}
        continueButtonText="Confirm"
        isCentered
        icon={<WarningIcon color="orange.100" />}
      />
    </>
  );
};
