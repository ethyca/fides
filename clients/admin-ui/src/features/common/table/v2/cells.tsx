import { HeaderContext } from "@tanstack/react-table";
import { formatDistance } from "date-fns";
import {
  AntButton as Button,
  AntInput as Input,
  AntSwitch as Switch,
  AntSwitchProps as SwitchProps,
  AntTag as Tag,
  AntTagProps as TagProps,
  AntTooltip as Tooltip,
  Checkbox,
  CheckboxProps,
  Flex,
  FlexProps,
  Text,
  TextProps,
  useDisclosure,
  useToast,
  WarningIcon,
} from "fidesui";
import { useField, useFormikContext } from "formik";
import { isBoolean } from "lodash";
import { ReactElement, ReactNode, useEffect, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import ConfirmationModal from "~/features/common/modals/ConfirmationModal";
import { errorToastParams } from "~/features/common/toast";
import { formatDate, sentenceCase } from "~/features/common/utils";
import { RTKResult } from "~/types/errors";

import { FidesCellProps, FidesCellState } from "./FidesCell";

export const DefaultCell = <T,>({
  value,
  cellProps,
  ...chakraStyleProps
}: {
  cellProps?: FidesCellProps<T>;
  value: string | ReactElement | undefined | number | null | boolean;
} & TextProps) => {
  const expandable = !!cellProps?.cell.column.columnDef.meta?.showHeaderMenu;
  const isExpanded = expandable && !!cellProps?.cellState?.isExpanded;
  return (
    <Text
      fontSize="xs"
      lineHeight={4}
      py={1.5}
      fontWeight="normal"
      textOverflow="ellipsis"
      overflow={isExpanded ? undefined : "hidden"}
      whiteSpace={isExpanded ? "normal" : undefined}
      title={isExpanded && !!value ? undefined : value?.toString()}
      {...chakraStyleProps}
    >
      {isBoolean(value) ? value.toString() : value}
    </Text>
  );
};

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
      <Tooltip title={formattedDate}>
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
  ...tagProps
}: {
  value: string | number | null | undefined;
  suffix?: string;
} & TagProps) => (
  <BadgeCellContainer>
    <Tag {...tagProps}>
      {value}
      {suffix}
    </Tag>
  </BadgeCellContainer>
);

export const BadgeCellCount = ({
  count,
  singSuffix,
  plSuffix,
  ...tagProps
}: {
  count: number;
  singSuffix?: string;
  plSuffix?: string;
} & TagProps) => {
  let tag = null;
  if (count === 1) {
    tag = (
      <Tag {...tagProps}>
        {count}
        {singSuffix ? ` ${singSuffix}` : null}
      </Tag>
    );
  } else {
    tag = (
      <Tag {...tagProps}>
        {count}
        {plSuffix ? ` ${plSuffix}` : null}
      </Tag>
    );
  }
  return <BadgeCellContainer>{tag}</BadgeCellContainer>;
};

type BadgeCellExpandableValues = { label: string | ReactNode; key: string }[];
export const BadgeCellExpandable = <T,>({
  values,
  cellProps,
  ...tagProps
}: {
  values: BadgeCellExpandableValues | undefined;
  cellProps?: Omit<FidesCellProps<T>, "onRowClick">;
} & TagProps) => {
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
          <Tag
            color="white"
            key={value.key}
            data-testid={value.key}
            {...tagProps}
          >
            {value.label}
          </Tag>
        ))}
        {isCollapsed && values && values.length > displayThreshold && (
          <Button
            type="link"
            size="small"
            onClick={() => setIsCollapsed(false)}
            className="text-xs font-normal"
          >
            +{values.length - displayThreshold} more
          </Button>
        )}
      </Flex>
    );
  }, [displayValues, isCollapsed, isWrappedState, values, tagProps]);
};

export const GroupCountBadgeCell = ({
  value,
  suffix,
  cellState,
  ignoreZero,
  tagProps,
}: {
  value: string[] | string | ReactNode | ReactNode[] | undefined;
  suffix?: string;
  cellState?: FidesCellState;
  ignoreZero?: boolean;
  tagProps?: TagProps;
}) => {
  let tags = null;
  if (!value) {
    return ignoreZero ? null : (
      <Tag {...tagProps}>0{suffix ? ` ${suffix}` : ""}</Tag>
    );
  }
  if (Array.isArray(value)) {
    if (value.length === 1) {
      tags = <Tag {...tagProps}>{value}</Tag>;
    } else if (cellState?.isExpanded && value.length > 0) {
      tags = value.map((d, i) => (
        <Tag key={d?.toString() || i} {...tagProps}>
          {d}
        </Tag>
      ));
    } else {
      tags = (
        <Tag {...tagProps}>
          {value.length}
          {suffix ? ` ${suffix}` : null}
        </Tag>
      );
    }
  } else {
    tags = <Tag {...tagProps}>{value}</Tag>;
  }

  return (
    <Flex alignItems="center" height="100%" gap={0} overflowX="hidden">
      {tags}
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
    <Checkbox data-testid={dataTestId || undefined} {...rest} />
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

export const EditableHeaderCell = <T,>({
  value,
  defaultValue,
  isEditing,
  ...props
}: DefaultHeaderCellProps<T> & {
  defaultValue: string;
  isEditing: boolean;
}) => {
  const headerId = props.column.columnDef.id || "";
  const [field] = useField(headerId);
  const { submitForm } = useFormikContext();
  return isEditing ? (
    <Input
      {...field}
      maxLength={80}
      placeholder={defaultValue}
      aria-label="Edit column name"
      size="small"
      data-testid={`column-${headerId}-input`}
      onPressEnter={submitForm}
    />
  ) : (
    <DefaultHeaderCell value={value} {...props} />
  );
};

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
