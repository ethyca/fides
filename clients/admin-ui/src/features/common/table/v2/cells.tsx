import { HeaderContext } from "@tanstack/react-table";
import { formatDistance } from "date-fns";
import {
  AntSwitch as Switch,
  AntSwitchProps as SwitchProps,
  Badge,
  BadgeProps,
  Box,
  Button,
  Checkbox,
  CheckboxProps,
  Flex,
  FlexProps,
  Text,
  TextProps,
  Tooltip,
  useDisclosure,
  useToast,
  WarningIcon,
} from "fidesui";
import { ReactNode, useEffect, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { errorToastParams } from "~/features/common/toast";
import { formatDate, sentenceCase } from "~/features/common/utils";
import { RTKResult } from "~/types/errors";

import { FidesCellProps, FidesCellState } from "./FidesCell";

export const DefaultCell = ({
  value,
  ...chakraStyleProps
}: {
  value: string | undefined | number | null | boolean;
} & TextProps) => (
  <Flex alignItems="center" height="100%">
    <Text
      fontSize="xs"
      lineHeight={4}
      fontWeight="normal"
      overflow="hidden"
      textOverflow="ellipsis"
      {...chakraStyleProps}
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
    boxShadow={
      props.variant === "outline"
        ? "inset 0 0 0px 1px var(--chakra-colors-gray-100)"
        : undefined
    }
    {...props}
  >
    {children}
  </Badge>
);

export const RelativeTimestampCell = ({
  time,
}: {
  time?: string | number | Date | null;
}) => {
  if (!time) {
    return <DefaultCell value="N/A" />;
  }

  const timestamp = formatDistance(new Date(time), new Date(), {
    addSuffix: true,
  });

  const formattedDate = formatDate(new Date(time));

  return (
    <Flex alignItems="center" height="100%">
      <Tooltip label={formattedDate} hasArrow>
        <Text
          fontSize="xs"
          lineHeight={4}
          fontWeight="normal"
          overflow="hidden"
          textOverflow="ellipsis"
        >
          {sentenceCase(timestamp)}
        </Text>
      </Tooltip>
    </Flex>
  );
};

export const BadgeCellContainer = ({ children, ...props }: FlexProps) => (
  <Flex alignItems="center" height="100%" mr={2} {...props}>
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

type BadgeCellExpandableValues = { label: string | ReactNode; key: string }[];
export const BadgeCellExpandable = <T,>({
  values,
  cellProps,
  ...badgeProps
}: {
  values: BadgeCellExpandableValues | undefined;
  cellProps?: Omit<FidesCellProps<T>, "onRowClick">;
} & BadgeProps) => {
  const { isExpanded, isWrapped, version } = cellProps?.cellState || {};
  const displayThreshold = 2; // Number of badges to display when collapsed
  const [isCollapsed, setIsCollapsed] = useState<boolean>(!isExpanded);
  const [isWrappedState, setIsWrappedState] = useState<boolean>(!!isWrapped);
  const [displayValues, setDisplayValues] = useState<
    BadgeCellExpandableValues | undefined
  >(!isExpanded ? values?.slice(0, displayThreshold) : values);

  useEffect(() => {
    // Also reset isCollapsed state when version changes.
    // This is to handle the case where the user expands cells individually.
    // "Expand/Collapse All" will not be reapplied otherwise.
    setIsCollapsed(!isExpanded);
  }, [isExpanded, version]);

  useEffect(() => {
    setIsWrappedState(!!isWrapped);
  }, [isWrapped]);

  useEffect(() => {
    if (values?.length) {
      setDisplayValues(
        isCollapsed ? values.slice(0, displayThreshold) : values,
      );
    }
  }, [isCollapsed, values]);

  return useMemo(() => {
    if (!displayValues?.length) {
      return null;
    }
    return (
      <Flex
        alignItems={isCollapsed ? "center" : "flex-start"}
        flexDirection={isCollapsed || isWrappedState ? "row" : "column"}
        flexWrap={isWrappedState ? "wrap" : "nowrap"}
        gap={1.5}
        pt={2}
        pb={2}
        onClick={(e) => {
          if (!isCollapsed) {
            e.stopPropagation();
            setIsCollapsed(true);
          }
        }}
        cursor={isCollapsed ? undefined : "pointer"}
      >
        {displayValues.map((value) => (
          <FidesBadge key={value.key} data-testid={value.key} {...badgeProps}>
            {value.label}
          </FidesBadge>
        ))}
        {isCollapsed && values && values.length > displayThreshold && (
          <Button
            variant="link"
            size="xs"
            fontWeight={400}
            onClick={() => setIsCollapsed(false)}
            display="inline-block" // prevents squishing the button on column resize
          >
            +{values.length - displayThreshold} more
          </Button>
        )}
      </Flex>
    );
  }, [displayValues, isCollapsed, isWrappedState, values, badgeProps]);
};

export const GroupCountBadgeCell = ({
  value,
  suffix,
  cellState,
  ignoreZero,
  badgeProps,
}: {
  value: string[] | string | ReactNode | ReactNode[] | undefined;
  suffix?: string;
  cellState?: FidesCellState;
  ignoreZero?: boolean;
  badgeProps?: BadgeProps;
}) => {
  let badges = null;
  if (!value) {
    return ignoreZero ? null : (
      <FidesBadge {...badgeProps}>0{suffix ? ` ${suffix}` : ""}</FidesBadge>
    );
  }
  if (Array.isArray(value)) {
    // If there's only one value, always display it
    if (value.length === 1) {
      badges = <FidesBadge {...badgeProps}>{value}</FidesBadge>;
    }
    // Expanded case, list every value as a badge
    else if (cellState?.isExpanded && value.length > 0) {
      badges = value.map((d, i) => (
        <Box key={d?.toString() || i} mr={2}>
          <FidesBadge {...badgeProps}>{d}</FidesBadge>
        </Box>
      ));
    }
    // Collapsed case, summarize the values in one badge
    else {
      badges = (
        <FidesBadge {...badgeProps}>
          {value.length}
          {suffix ? ` ${suffix}` : null}
        </FidesBadge>
      );
    }
  } else {
    badges = <FidesBadge {...badgeProps}>{value}</FidesBadge>;
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

  const handleToggle = async (checked: boolean) => {
    if (checked) {
      await handlePatch({ enable: true });
    } else {
      modal.onOpen();
    }
  };

  return (
    <>
      <Switch
        checked={enabled}
        onChange={handleToggle}
        disabled={isDisabled}
        data-testid="toggle-switch"
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
