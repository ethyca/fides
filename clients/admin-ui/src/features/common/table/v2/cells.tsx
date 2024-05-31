import { HeaderContext } from "@tanstack/react-table";
import { formatDistance } from "date-fns";
import {
  Badge,
  Box,
  Checkbox,
  CheckboxProps,
  Flex,
  Switch,
  SwitchProps,
  Text,
  TextProps,
  useDisclosure,
  useToast,
  WarningIcon,
} from "fidesui";
import { ChangeEvent, FC, ReactNode } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { errorToastParams } from "~/features/common/toast";
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

export const RelativeTimestampCell = ({
  time,
}: {
  time?: string | number | Date;
}) => {
  if (!time) {
    return <DefaultCell value="N/A" />;
  }
  return (
    <DefaultCell
      value={formatDistance(new Date(time), new Date(), {
        addSuffix: true,
      })}
    />
  );
};

export const BadgeCellContainer = ({ children }: { children: ReactNode }) => (
  <Flex alignItems="center" height="100%" mr={2}>
    {children}
  </Flex>
);

export const BadgeCell = ({
  value,
  suffix,
}: {
  value: string | number;
  suffix?: string;
}) => (
  <BadgeCellContainer>
    <FidesBadge>
      {value}
      {suffix ? ` ${suffix}` : null}
    </FidesBadge>
  </BadgeCellContainer>
);

export const GroupCountBadgeCell = ({
  value,
  suffix,
  isDisplayAll,
}: {
  value: string[] | string | ReactNode | ReactNode[] | undefined;
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
  <Flex
    alignItems="center"
    justifyContent="center"
    onClick={(e) => e.stopPropagation()}
  >
    <Checkbox
      data-testid={dataTestId || undefined}
      {...rest}
      colorScheme="purple"
    />
  </Flex>
);

type DefaultHeaderCellProps<T, V> = {
  value: V;
} & HeaderContext<T, V> &
  TextProps;

export const DefaultHeaderCell = <T,>({
  value,
  ...props
}: DefaultHeaderCellProps<
  T,
  string | number | string[] | undefined | boolean
>) => (
  <Text fontSize="xs" lineHeight={9} fontWeight="medium" {...props}>
    {value}
  </Text>
);

interface EnableCellProps extends Omit<SwitchProps, "value"> {
  enabled: boolean;
  onToggle: (data: boolean) => Promise<RTKResult>;
  title: string;
  message: string;
  isDisabled?: boolean;
}

export const EnableCell = ({
  enabled,
  onToggle,
  title,
  message,
  isDisabled,
  ...switchProps
}: EnableCellProps) => {
  const modal = useDisclosure();
  const toast = useToast();
  const handlePatch = async ({ enable }: { enable: boolean }) => {
    const result = await onToggle(enable);
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    }
  };

  const handleToggle = async (event: ChangeEvent<HTMLInputElement>) => {
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
        isChecked={enabled}
        data-testid="toggle-switch"
        disabled={isDisabled}
        onChange={handleToggle}
        {...switchProps}
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
