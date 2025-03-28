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

  // Map common action types with proper capitalization
  const actionTypeMap: Record<string, string> = {
    access: "Access",
    erasure: "Erasure",
    deletion: "Erasure",
  };

  const key = actionType.toLowerCase();
  return (
    actionTypeMap[key] ||
    actionType
      .split("_")
      .map((word) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase())
      .join(" ")
  );
};

// Simple components for table cells
const EmptyTableNotice = () => (
  <Center py={10}>
    <Text>No policies found</Text>
  </Center>
);

const KeyBadgeCell = ({ getValue }: { getValue: () => string | null }) => {
  const value = getValue();
  return !value ? (
    <DefaultCell value="-" />
  ) : (
    <BadgeCell value={value} color="marble" />
  );
};

const ActionTypeBadgeCell = ({
  getValue,
}: {
  getValue: () => string | null;
}) => {
  const value = getValue();
  const displayText = formatActionType(value);

  // Choose color based on action type
  const colorMap: Record<string, string> = {
    access: "success",
    deletion: "terracotta",
    erasure: "terracotta",
  };

  const key = value?.toLowerCase() || "consent";
  const color = colorMap[key] || "minos";

  return <BadgeCell value={displayText} color={color} />;
};

const TimeframeBadgeCell = ({
  getValue,
}: {
  getValue: () => number | null;
}) => {
  const value = getValue();
  return value ? (
    <DefaultCell value={`${value} days`} />
  ) : (
    <DefaultCell value="-" />
  );
};

// Action cell for policies
const PolicyActionsCell = ({
  policy,
  onViewRules,
}: {
  policy: PolicyResponse;
  onViewRules: (policy: PolicyResponse) => void;
}) => (
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

  // Filter out policies with null drp_action
  const validPolicies = useMemo(
    () => (data?.items || []).filter((policy) => policy.drp_action !== null),
    [data],
  );

  // Apply search filter
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

  // Handle policy row click
  const handleRowClick = useCallback(
    (policy: PolicyResponse) => {
      router.push({
        pathname: "/policies/[policyKey]",
        query: { policyKey: policy.key || encodeURIComponent(policy.name) },
      });
    },
    [router],
  );

  // Define table columns
  const columns = useMemo(
    () =>
      [
        columnHelper.accessor((row) => row.name, {
          id: "name",
          cell: (props) => <DefaultCell value={props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Policy Name" {...props} />
          ),
          size: 180,
        }),
        columnHelper.accessor((row) => row.key, {
          id: "key",
          cell: (props) => <KeyBadgeCell getValue={() => props.getValue()} />,
          header: (props) => (
            <DefaultHeaderCell value="Policy Key" {...props} />
          ),
          size: 150,
        }),
        columnHelper.accessor((row) => row.drp_action, {
          id: "drp_action",
          cell: (props) => (
            <ActionTypeBadgeCell getValue={() => props.getValue()} />
          ),
          header: (props) => (
            <DefaultHeaderCell value="Action Type" {...props} />
          ),
          size: 150,
        }),
        columnHelper.accessor((row) => row.execution_timeframe, {
          id: "execution_timeframe",
          cell: (props) => (
            <TimeframeBadgeCell getValue={() => props.getValue()} />
          ),
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
