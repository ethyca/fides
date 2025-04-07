import {
  AntButton as Button,
  AntFlex as Flex,
  AntFlexProps as FlexProps,
  AntTag as Tag,
  Skeleton,
  Text,
} from "fidesui";
import NextLink from "next/link";

import { useAppSelector } from "~/app/hooks";
import { selectPurposes } from "~/features/common/purpose.slice";
import { TCFConfigurationDetail } from "~/types/api";

import { FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS } from "./constants";

interface FauxTableCellProps extends FlexProps {
  borderLeft?: boolean;
  borderRight?: boolean;
  width?: string;
}
const FauxTableCell = ({
  width,
  style,
  borderLeft = false,
  borderRight = false,
  ...props
}: FauxTableCellProps) => (
  <Flex
    align="center"
    className="h-full px-4"
    {...props}
    style={{
      borderLeft: borderLeft ? "solid 1px" : "none",
      borderRight: borderRight ? "solid 1px" : "none",
      borderColor: "var(--ant-color-border)",
      width,
      ...style,
    }}
    role="cell"
  />
);

interface FauxColumnHeaderProps extends FlexProps {
  borderLeft?: boolean;
  width?: string;
}

const FauxColumnHeader = ({
  width,
  style,
  borderLeft = false,
  children,
  ...props
}: FauxColumnHeaderProps) => (
  <Flex
    align="center"
    role="columnheader"
    className="px-4"
    {...props}
    style={{
      borderLeft: borderLeft ? "solid 1px" : "none",
      borderColor: "var(--ant-color-border)",
      width,
      ...style,
    }}
  >
    <Text fontWeight="medium">{children}</Text>
  </Flex>
);

interface FauxRowProps extends FlexProps {
  isHeader?: boolean;
  isLastRow?: boolean;
}

const FauxRow = ({
  isHeader = false,
  isLastRow = false,
  style,
  ...props
}: FauxRowProps) => (
  <Flex
    role={isHeader ? "rowheader" : "row"}
    className="h-9 w-full"
    {...props}
    style={{
      backgroundColor: isHeader ? "var(--fidesui-bg-default)" : undefined,
      borderBottom: isLastRow ? "none" : "solid 1px",
      borderColor: "var(--ant-color-border)",
      ...style,
    }}
  />
);

interface PublisherRestrictionsTableProps extends Omit<FlexProps, "children"> {
  config?: TCFConfigurationDetail;
  isLoading?: boolean;
}

export const PublisherRestrictionsTable = ({
  config,
  isLoading,
  style,
  ...props
}: PublisherRestrictionsTableProps): JSX.Element => {
  const { purposes } = useAppSelector(selectPurposes);

  return (
    <Flex
      vertical
      {...props}
      style={{
        maxWidth: "1200px",
        border: "solid 1px",
        borderColor: "var(--ant-color-border)",
        backgroundColor: "var(--ant-color-bg-base)",
        fontSize: "12px",
        ...style,
      }}
      aria-label="Publisher restrictions table"
      role="table"
    >
      <FauxRow
        isHeader
        style={{
          width: "100%",
        }}
      >
        <FauxColumnHeader width="600px">TCF purpose</FauxColumnHeader>
        <FauxColumnHeader flex={1} borderLeft>
          Restrictions
        </FauxColumnHeader>
        <FauxColumnHeader width="100px" borderLeft>
          Flexible
        </FauxColumnHeader>
        <FauxColumnHeader width="100px" borderLeft>
          Actions
        </FauxColumnHeader>
      </FauxRow>
      {Object.values(purposes).map((purpose, index) => (
        <FauxRow
          key={purpose.id}
          isLastRow={index === Object.values(purposes).length - 1}
        >
          <FauxTableCell width="600px">
            Purpose {purpose.id}: {purpose.name}
          </FauxTableCell>
          <FauxTableCell flex={1} borderLeft>
            {isLoading ? (
              <Skeleton height="16px" width="100%" />
            ) : (
              config?.restriction_types_per_purpose?.[purpose.id] || "none"
            )}
          </FauxTableCell>
          <FauxTableCell width="100px" borderLeft>
            {FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(purpose.id) ? (
              <Tag color="error">No</Tag>
            ) : (
              <Tag color="success">Yes</Tag>
            )}
          </FauxTableCell>
          <FauxTableCell width="100px" borderLeft>
            {FORBIDDEN_LEGITIMATE_INTEREST_PURPOSE_IDS.includes(purpose.id) ? (
              <div />
            ) : (
              <NextLink
                href={`/settings/consent/${config?.id}/${purpose.id}`}
                passHref
                legacyBehavior
              >
                <Button size="small">Edit</Button>
              </NextLink>
            )}
          </FauxTableCell>
        </FauxRow>
      ))}
    </Flex>
  );
};
