import {
  ColumnDef,
  createColumnHelper,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { AntButton as Button, Box, Center, Spinner, Text } from "fidesui";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useMemo } from "react";

import FixedLayout from "~/features/common/FixedLayout";
import { PRIVACY_POLICY_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import {
  DefaultCell,
  DefaultHeaderCell,
  FidesTableV2,
} from "~/features/common/table/v2";
import {
  BadgeCell,
  BadgeCellExpandable,
} from "~/features/common/table/v2/cells";
import {
  useGetPoliciesQuery,
  useGetPolicyRulesQuery,
} from "~/features/policy/policy.slice";
import { DrpAction, RuleResponseWithTargets } from "~/types/api";

type TargetItem = {
  label: string;
  key: string;
};

// Column helper with proper typing
const columnHelper = createColumnHelper<RuleResponseWithTargets>();

// Handle empty state when no rules are found
const EmptyTableNotice = ({
  hasRulesButAllFiltered = false,
}: {
  hasRulesButAllFiltered?: boolean;
}) => (
  <Center py={10}>
    <Text>
      {hasRulesButAllFiltered
        ? "All rules for this policy have been filtered out."
        : "No rules found for this policy."}
    </Text>
  </Center>
);

// Basic cell components
const NameCell = ({ getValue }: { getValue: () => string | null }) => (
  <DefaultCell value={getValue() || "-"} />
);

const NameHeader = ({ ...props }: any) => (
  <DefaultHeaderCell value="Rule Name" {...props} />
);

// Function to format action types to be more readable
const formatActionType = (actionType: string | null): string => {
  if (!actionType) {
    return "-";
  }

  // Map common action types with proper capitalization
  const actionTypeMap: Record<string, string> = {
    access: "Access",
    erasure: "Erasure",
    deletion: "Erasure",
    consent: "Consent",
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

// Choose color based on action type
const actionColorMap: Record<string, string> = {
  access: "success",
  deletion: "terracotta",
  erasure: "terracotta",
};

// Action type cell component
const ActionTypeCell = ({ getValue }: { getValue: () => string | null }) => {
  const actionType = getValue();
  if (!actionType) {
    return <DefaultCell value="-" />;
  }

  const key = actionType.toLowerCase();
  const color = actionColorMap[key] || "gray";
  return <BadgeCell value={formatActionType(actionType)} color={color} />;
};

const ActionTypeHeader = (props: any) => (
  <DefaultHeaderCell value="Action Type" {...props} />
);

// Masking strategy cell components
const MaskingStrategyCell = ({ getValue }: { getValue: () => any }) => {
  const data = getValue();
  const value = data.strategy;

  if (!value || value === "not_applicable") {
    return (
      <DefaultCell
        value={value ? "Not applicable" : "None specified"}
        color="gray.500"
      />
    );
  }

  // Map masking strategies to colors and display names
  const strategyMap: Record<string, { color: string; displayName: string }> = {
    null_rewrite: { color: "error", displayName: "Null Rewrite" },
    string_rewrite: { color: "success", displayName: "String Rewrite" },
    hash: { color: "minos", displayName: "Hash" },
    hmac: { color: "caution", displayName: "HMAC" },
    random_string_rewrite: { color: "alert", displayName: "Random String" },
    aes_encrypt: { color: "info", displayName: "AES Encrypt" },
  };

  const strategy = strategyMap[value] || { color: "minos", displayName: value };
  return <BadgeCell value={strategy.displayName} color={strategy.color} />;
};

// Masking strategy renderer
const MaskingStrategyCellRenderer = ({
  getValue,
  row,
}: {
  getValue: () => any;
  row: any;
}) => {
  const value = getValue();
  const getCellValue = () => ({
    strategy: value,
    rowData: row.original,
  });
  return <MaskingStrategyCell getValue={getCellValue} />;
};

const MaskingStrategyHeaderCell = (props: any) => (
  <DefaultHeaderCell value="Masking Strategy" {...props} />
);

// Targets cell component
const TargetsCell = ({ getValue }: { getValue: () => TargetItem[] }) => {
  const targets = getValue();

  if (!targets?.length) {
    return <DefaultCell value="-" />;
  }

  return (
    <Box
      maxWidth="100%"
      overflowX="visible"
      overflowY="visible"
      whiteSpace="normal"
      py={1}
    >
      <BadgeCellExpandable values={targets} />
    </Box>
  );
};

// Wrapper component for the targets cell
const TargetsCellWrapper = ({ getValue }: { getValue: () => any }) => {
  return <TargetsCell getValue={getValue} />;
};

const TargetsHeader = ({ ...props }: any) => (
  <DefaultHeaderCell value="Targets" {...props} />
);

// Helper to extract masking strategy
const extractMaskingStrategy = (rule: any): string | null => {
  if (!rule.masking_strategy) {
    return null;
  }

  return typeof rule.masking_strategy === "string"
    ? rule.masking_strategy
    : rule.masking_strategy.strategy || null;
};

const PolicyDetailPage: NextPage = () => {
  const router = useRouter();
  const policyKey = router.query.policyKey as string;

  // Fetch policy data
  const { data: policiesData, isLoading: isPoliciesLoading } =
    useGetPoliciesQuery();
  const { data: rulesData, isLoading: isRulesLoading } = useGetPolicyRulesQuery(
    { policyKey },
    { skip: !policyKey },
  );

  // Find the current policy
  const policy = useMemo(() => {
    if (!policiesData?.items || !policyKey) {
      return null;
    }

    return policiesData.items.find(
      (p) => p.key === policyKey || p.name === decodeURIComponent(policyKey),
    );
  }, [policiesData, policyKey]);

  // Filter and format rules
  const rules = useMemo(() => {
    // No policy or rules data
    if (!policy) {
      return [];
    }

    // Get rules from API response or policy object
    const sourceRules = rulesData?.items?.length
      ? rulesData.items
      : policy.rules || [];

    // Filter out consent rules and null drp_action rules
    return sourceRules
      .filter(
        (rule) =>
          rule.action_type?.toLowerCase() !== "consent" &&
          (rule as any).drp_action !== null,
      )
      .map((rule) => {
        // If using policy.rules, we need to add targets
        if (!rulesData?.items?.length && policy.rules?.includes(rule)) {
          return {
            ...rule,
            targets:
              rulesData?.items?.find((r) => r.key === rule.key)?.targets || [],
          };
        }
        return rule;
      });
  }, [rulesData, policy]);

  // Define table columns
  const columns = useMemo(() => {
    const baseColumns: ColumnDef<RuleResponseWithTargets, any>[] = [
      columnHelper.accessor((row) => row.name, {
        id: "name",
        cell: NameCell,
        header: NameHeader,
        size: 150,
      }),
      columnHelper.accessor((row) => row.action_type, {
        id: "action_type",
        cell: ActionTypeCell,
        header: ActionTypeHeader,
        size: 120,
      }),
    ];

    // Add masking strategy column for deletion policies
    if (policy?.drp_action === DrpAction.DELETION) {
      baseColumns.push(
        columnHelper.accessor((row) => extractMaskingStrategy(row), {
          id: "masking_strategy",
          cell: MaskingStrategyCellRenderer,
          header: MaskingStrategyHeaderCell,
          size: 130,
        }),
      );
    }

    // Add targets column
    baseColumns.push({
      id: "targets",
      header: TargetsHeader,
      cell: TargetsCellWrapper,
      size: 450,
      accessorFn: (row) => {
        const targets = row.targets || [];
        return targets.map((t) => ({
          label: t.data_category,
          key: t.data_category,
        }));
      },
    });

    return baseColumns;
  }, [policy?.drp_action]);

  // Table instance
  const tableInstance = useReactTable<RuleResponseWithTargets>({
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    columns,
    data: rules,
    columnResizeMode: "onChange",
    defaultColumn: {
      minSize: 80,
      maxSize: 1000,
    },
  });

  // Loading state
  if (isPoliciesLoading || isRulesLoading) {
    return (
      <FixedLayout title="Loading Policy...">
        <Center height="80vh">
          <Spinner size="xl" />
        </Center>
      </FixedLayout>
    );
  }

  // Policy not found
  if (!policy) {
    return (
      <FixedLayout title="Policy Not Found">
        <Center height="50vh" flexDirection="column" gap={4}>
          <Text fontSize="xl">Policy not found</Text>
          <Button onClick={() => router.push(PRIVACY_POLICY_ROUTE)}>
            Back to Policies
          </Button>
        </Center>
      </FixedLayout>
    );
  }

  return (
    <FixedLayout title={`Policy - ${policy.name}`}>
      <PageHeader
        heading="Request policy rules"
        breadcrumbItems={[
          { title: "All request policies", href: PRIVACY_POLICY_ROUTE },
          { title: policy.name },
        ]}
        data-testid="policy-details"
      />

      <Box className="mb-4">
        <Text fontSize="sm" color="gray.600" className="mb-2">
          {policy.drp_action === DrpAction.DELETION ? (
            <>
              Rules define how data is processed for this policy. For deletion
              policies, masking strategies specify how data should be
              transformed or removed. Different strategies apply different
              transformations to the data.
            </>
          ) : (
            <>
              Rules define how data is processed for this policy. Each rule
              specifies which data categories are affected and how they should
              be handled.
            </>
          )}
        </Text>
      </Box>

      {rules.length === 0 ? (
        <EmptyTableNotice
          hasRulesButAllFiltered={policy?.rules?.some(
            (rule) => rule.action_type?.toLowerCase() === "consent",
          )}
        />
      ) : (
        <Box data-testid="policy-rules-table" className="overflow-visible">
          <FidesTableV2
            tableInstance={tableInstance}
            emptyTableNotice={<EmptyTableNotice />}
          />
        </Box>
      )}
    </FixedLayout>
  );
};

export default PolicyDetailPage;
