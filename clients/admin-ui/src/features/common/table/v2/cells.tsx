import { HeaderContext } from "@tanstack/react-table";
import { formatDistance } from "date-fns";
import {
  Badge,
  BadgeProps,
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
import { ChangeEvent, ReactNode } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { errorToastParams } from "~/features/common/toast";
import { sentenceCase } from "~/features/common/utils";
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

const FidesBadge = ({ children, ...props }: BadgeProps) => (
  <Badge
    textTransform="none"
    fontWeight="400"
    fontSize="xs"
    lineHeight={4}
    color="gray.600"
    px={2}
    py={1}
    {...props}
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

  const timestamp = formatDistance(new Date(time), new Date(), {
    addSuffix: true,
  });

  return <DefaultCell value={sentenceCase(timestamp)} />;
};

export const BadgeCellContainer = ({ children }: { children: ReactNode }) => (
  <Flex alignItems="center" height="100%" mr={2}>
    {children}
  </Flex>
);

export const BadgeCell = ({
  value,
  suffix,
  ...badgeProps
}: {
  value: string | number;
  suffix?: string;
} & BadgeProps) => (
  <BadgeCellContainer>
    <FidesBadge {...badgeProps}>
      {value}
      {suffix}
    </FidesBadge>
  </BadgeCellContainer>
);

export const BadgeCellCount = ({
  count,
  singSuffix,
  plSuffix,
  ...badgeProps
}: {
  count: number;
  singSuffix?: string;
  plSuffix?: string;
} & BadgeProps) => {
  // If count is 1, display count with singular suffix
  let badge = null;
  if (count === 1) {
    badge = (
      <FidesBadge {...badgeProps}>
        {count}
        {singSuffix ? ` ${singSuffix}` : null}
      </FidesBadge>
    );
  }
  // If count is 0 or > 1, display count with plural suffix
  else {
    badge = (
      <FidesBadge {...badgeProps}>
        {count}
        {plSuffix ? ` ${plSuffix}` : null}
      </FidesBadge>
    );
  }
  return <BadgeCellContainer>{badge}</BadgeCellContainer>;
};

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
      badges = value.map((d, i) => (
        <Box key={d?.toString() || i} mr={2}>
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

type DefaultHeaderCellProps<T> = {
  value: string | number | string[] | undefined | boolean;
} & HeaderContext<T, unknown> &
  TextProps;

export const DefaultHeaderCell = <T,>({
  value,
  ...props
}: DefaultHeaderCellProps<T>) => (
  <Text fontSize="xs" lineHeight={9} fontWeight="medium" flex={1} {...props}>
    {value}
  </Text>
);

interface EnableCellProps extends Omit<SwitchProps, "value" | "onToggle"> {
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
        isDisabled={isDisabled}
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
