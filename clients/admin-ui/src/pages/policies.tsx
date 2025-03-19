/* eslint-disable react/no-unstable-nested-components */
import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { AntButton as Button, Box, Center, Link, Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { GearLightIcon } from "~/features/common/Icon";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
  GlobalFilterV2,
  TableActionBar,
  TableSkeletonLoader,
} from "~/features/common/table/v2";
import { BadgeCell } from "~/features/common/table/v2/cells";
import { useGetPoliciesQuery } from "~/features/policy/policy.slice";
import { PolicyResponse } from "~/types/api";

const columnHelper = createColumnHelper<PolicyResponse>();

// Function to format action types to be more readable
const formatActionType = (actionType: string | null): string => {
  if (!actionType) {
    return "Consent";
  }

  // Map action types to more readable values with proper capitalization
  switch (actionType.toLowerCase()) {
    case "access":
      return "Access";
    case "erasure":
    case "deletion":
      return "Erasure";
    case "consent":
      return "Consent";
    case "sale:opt_out":
      return "Sale Opt-Out";
    case "sale:opt_in":
      return "Sale Opt-In";
    case "access:categories":
      return "Access Categories";
    case "access:specific":
      return "Access Specific";
    default:
      // Convert snake_case to Title Case
      return actionType
        .split("_")
        .map(
          (word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase(),
        )
        .join(" ");
  }
};

const EmptyTableNotice = () => (
  <Center py={10}>
    <Text>No policies found</Text>
  </Center>
);

// Define badge cell for policy keys
const KeyBadgeCell = ({ getValue }: { getValue: () => string | null }) => {
  const value = getValue();
  if (!value) {
    return <DefaultCell value="-" />;
  }
  return <BadgeCell value={value} color="marble" />;
};

// Action type badge cell that shows the action type in a colored badge
const ActionTypeBadgeCell = ({
  getValue,
}: {
  getValue: () => string | null;
}) => {
  const value = getValue();
  if (!value) {
    return <BadgeCell value="Consent" color="caution" />;
  }

  // Format the display text
  const displayText = formatActionType(value);

  // Choose color based on action type
  let color;
  switch (value.toLowerCase()) {
    case "access":
      color = "success";
      break;
    case "deletion":
    case "erasure":
      color = "error";
      break;
    case "consent":
      color = "success";
      break;
    case "sale:opt_out":
    case "sale:opt_in":
      color = "alert";
      break;
    default:
      color = "minos";
  }

  return <BadgeCell value={displayText} color={color} />;
};

// Execution timeframe badge cell
const TimeframeBadgeCell = ({
  getValue,
}: {
  getValue: () => number | null;
}) => {
  const value = getValue();
  if (!value) {
    return <DefaultCell value="-" />;
  }

  return <DefaultCell value={`${value} days`} />;
};

// Action cell for policies
const PolicyActionsCell = ({
  policy,
  onViewRules,
}: {
  policy: PolicyResponse;
  onViewRules: (policy: PolicyResponse) => void;
}) => {
  return (
    <Button
      aria-label="View rules"
      icon={<GearLightIcon />}
      onClick={(e) => {
        e.stopPropagation();
        onViewRules(policy);
      }}
      data-testid={`view-rules-${policy.key || policy.name}`}
      size="small"
    >
      View rules
    </Button>
  );
};

const PoliciesPage: NextPage = () => {
  const router = useRouter();
  const { data, isLoading } = useGetPoliciesQuery();
  const [globalFilter, setGlobalFilter] = useState<string>();

  const updateGlobalFilter = useCallback(
    (searchTerm: string) => {
      setGlobalFilter(searchTerm);
    },
    [setGlobalFilter],
  );

  const policies = useMemo(() => data?.items || [], [data]);

  // Filter out policies with null drp_action
  const validPolicies = useMemo(() => {
    return policies.filter((policy) => policy.drp_action !== null);
  }, [policies]);

  const filteredPolicies = useMemo(() => {
    if (!globalFilter) {
      return validPolicies;
    }

    const lowerCaseFilter = globalFilter.toLowerCase();
    return validPolicies.filter(
      (policy) =>
        policy.name.toLowerCase().includes(lowerCaseFilter) ||
        (policy.key && policy.key.toLowerCase().includes(lowerCaseFilter)) ||
        (policy.drp_action &&
          policy.drp_action.toLowerCase().includes(lowerCaseFilter)),
    );
  }, [validPolicies, globalFilter]);

  const handleRowClick = useCallback(
    (policy: PolicyResponse) => {
      // Navigate to policy detail page
      router.push({
        pathname: "/policies/[policyKey]",
        query: { policyKey: policy.key || encodeURIComponent(policy.name) },
      });
    },
    [router],
  );

  // eslint-disable-next-line react/jsx-no-useless-fragment, react-hooks/exhaustive-deps
  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          // eslint-disable-next-line react/jsx-no-useless-fragment
          cell: (props) => <DefaultCell value={props.getValue()} />,
          // eslint-disable-next-line react/jsx-no-useless-fragment
          header: (props) => (
            <DefaultHeaderCell value="Policy Name" {...props} />
          ),
          size: 180,
        }),
        columnHelper.accessor((row) => row.key, {
          id: "key",
          // eslint-disable-next-line react/jsx-no-useless-fragment
          cell: (props) => <KeyBadgeCell getValue={() => props.getValue()} />,
          // eslint-disable-next-line react/jsx-no-useless-fragment
          header: (props) => (
            <DefaultHeaderCell value="Policy Key" {...props} />
          ),
          size: 150,
        }),
        columnHelper.accessor((row) => row.drp_action, {
          id: "drp_action",
          // eslint-disable-next-line react/jsx-no-useless-fragment
          cell: (props) => (
            <ActionTypeBadgeCell getValue={() => props.getValue()} />
          ),
          // eslint-disable-next-line react/jsx-no-useless-fragment
          header: (props) => (
            <DefaultHeaderCell value="Action Type" {...props} />
          ),
          size: 150,
        }),
        columnHelper.accessor((row) => row.execution_timeframe, {
          id: "execution_timeframe",
          // eslint-disable-next-line react/jsx-no-useless-fragment
          cell: (props) => (
            <TimeframeBadgeCell getValue={() => props.getValue()} />
          ),
          // eslint-disable-next-line react/jsx-no-useless-fragment
          header: (props) => (
            <DefaultHeaderCell value="Execution Timeframe" {...props} />
          ),
          size: 180,
        }),
        columnHelper.display({
          id: "actions",
          header: (props) => <DefaultHeaderCell value="Actions" {...props} />,
          cell: ({ row }) => (
            <PolicyActionsCell
              policy={row.original}
              onViewRules={handleRowClick}
            />
          ),
          meta: {
            disableRowClick: true,
          },
          size: 120,
        }),
      ] as ColumnDef<PolicyResponse, any>[],
    [handleRowClick],
  );

  const tableInstance = useReactTable<PolicyResponse>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: filteredPolicies,
    columnResizeMode: "onChange",
  });

  return (
    <FixedLayout title="Request policies">
      <PageHeader heading="Request policies" data-testid="privacy-policies" />

      <Box mb={4}>
        <Text fontSize="sm" color="gray.600">
          Request policies and rules must be created via the Fides API. See{" "}
          <Link
            href="https://ethyca.com/docs/dev-docs/configuration/policies/request-policies"
            color="blue.500"
            textDecoration="underline"
            isExternal
          >
            documentation
          </Link>{" "}
          for details.
        </Text>
      </Box>

      {isLoading ? (
        <TableSkeletonLoader rowHeight={36} numRows={15} />
      ) : (
        <Box data-testid="policy-table">
          <TableActionBar>
            <GlobalFilterV2
              globalFilter={globalFilter}
              setGlobalFilter={updateGlobalFilter}
              placeholder="Search"
              testid="policy-search"
            />
          </TableActionBar>
          <FidesTableV2
            tableInstance={tableInstance}
            emptyTableNotice={<EmptyTableNotice />}
          />
        </Box>
      )}
    </FixedLayout>
  );
};

export default PoliciesPage;
