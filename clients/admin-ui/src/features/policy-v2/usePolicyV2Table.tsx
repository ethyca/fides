import {
  Button,
  ColumnsType,
  Empty,
  Flex,
  Icons,
  Switch,
  Tag,
  Tooltip,
  useChakraToast as useToast,
} from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useMemo, useState } from "react";

import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { POLICIES_V2_ROUTE } from "~/features/common/nav/routes";
import { useHasPermission } from "~/features/common/Restrict";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { useAntTable, useTableState } from "~/features/common/table/hooks";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useDeletePolicyV2Mutation,
  useEvaluatePolicyMutation,
  useGetAllPoliciesV2Query,
  useUpdatePolicyV2Mutation,
} from "~/features/policy-v2/policy-v2.slice";
import {
  EvaluateResponse,
  EvaluateSubjectContext,
  PolicyV2,
} from "~/features/policy-v2/types";
import { ScopeRegistryEnum } from "~/types/api";

const EmptyTableNotice = () => {
  const router = useRouter();

  return (
    <Empty
      image={Empty.PRESENTED_IMAGE_SIMPLE}
      description={
        <Flex vertical gap="small">
          <div>No policies found.</div>
          <div>
            <Button
              onClick={() => router.push(`${POLICIES_V2_ROUTE}/new`)}
              type="primary"
              size="small"
              data-testid="add-policy-v2-btn"
              icon={<Icons.Add />}
              iconPosition="end"
            >
              Add a policy
            </Button>
          </div>
        </Flex>
      }
    />
  );
};

const usePolicyV2Table = () => {
  const toast = useToast();
  const userCanUpdate = useHasPermission([ScopeRegistryEnum.POLICY_V2_UPDATE]);
  const userCanDelete = useHasPermission([ScopeRegistryEnum.POLICY_V2_DELETE]);
  const userCanEvaluate = useHasPermission([ScopeRegistryEnum.EVALUATE_READ]);

  // Options modal state (shown before evaluation)
  const [isOptionsModalOpen, setIsOptionsModalOpen] = useState(false);
  const [pendingPolicyKey, setPendingPolicyKey] = useState<string | undefined>(
    undefined
  );
  const [pendingPolicyName, setPendingPolicyName] = useState<
    string | undefined
  >(undefined);

  // Evaluation results modal state
  const [isEvaluateModalOpen, setIsEvaluateModalOpen] = useState(false);
  const [evaluateResults, setEvaluateResults] =
    useState<EvaluateResponse | null>(null);
  const [evaluatingPolicyName, setEvaluatingPolicyName] = useState<
    string | undefined
  >(undefined);
  const [isEvaluating, setIsEvaluating] = useState(false);

  const tableState = useTableState({
    pagination: {
      defaultPageSize: 25,
      pageSizeOptions: [25, 50, 100],
    },
  });

  // Fetch data
  const { data, isLoading, isFetching } = useGetAllPoliciesV2Query({});
  const [updatePolicy] = useUpdatePolicyV2Mutation();
  const [deletePolicy] = useDeletePolicyV2Mutation();
  const [evaluatePolicy] = useEvaluatePolicyMutation();

  const items = useMemo(() => data?.items ?? [], [data?.items]);
  const dataSource = useMemo(
    () =>
      items.map((item) => ({
        ...item,
        ruleCount: item.rules?.length ?? 0,
      })),
    [items],
  );

  const totalRows = data?.total ?? 0;

  const handleToggleEnabled = async (policy: PolicyV2) => {
    const result = await updatePolicy({
      fides_key: policy.fides_key,
      enabled: !policy.enabled,
    });
    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(
        successToastParams(
          `Policy ${!policy.enabled ? "enabled" : "disabled"}`,
        ),
      );
    }
  };

  const handleDelete = async (fidesKey: string) => {
    // eslint-disable-next-line no-alert
    if (window.confirm("Are you sure you want to delete this policy?")) {
      const result = await deletePolicy(fidesKey);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(successToastParams("Policy deleted"));
      }
    }
  };

  // Show options modal for single policy evaluation
  const handleEvaluateSinglePolicy = useCallback(
    (policyKey: string, policyName: string) => {
      setPendingPolicyKey(policyKey);
      setPendingPolicyName(policyName);
      setIsOptionsModalOpen(true);
    },
    []
  );

  // Show options modal for all policies evaluation
  const handleEvaluateAllPolicies = useCallback(() => {
    setPendingPolicyKey(undefined);
    setPendingPolicyName(undefined);
    setIsOptionsModalOpen(true);
  }, []);

  // Close the options modal
  const handleCloseOptionsModal = useCallback(() => {
    setIsOptionsModalOpen(false);
    setPendingPolicyKey(undefined);
    setPendingPolicyName(undefined);
  }, []);

  // Run the actual evaluation after options are submitted
  const handleRunEvaluation = useCallback(
    async (subjectContext?: EvaluateSubjectContext) => {
      setIsOptionsModalOpen(false);
      setIsEvaluating(true);
      setEvaluatingPolicyName(pendingPolicyName);
      setEvaluateResults(null);
      setIsEvaluateModalOpen(true);

      // Build the request with optional context
      const request: { policy_key?: string; context?: { subject: EvaluateSubjectContext } } = {};
      if (pendingPolicyKey) {
        request.policy_key = pendingPolicyKey;
      }
      if (subjectContext) {
        request.context = { subject: subjectContext };
      }

      const result = await evaluatePolicy(request);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        setIsEvaluateModalOpen(false);
      } else {
        setEvaluateResults(result.data);
      }
      setIsEvaluating(false);
      setPendingPolicyKey(undefined);
      setPendingPolicyName(undefined);
    },
    [evaluatePolicy, pendingPolicyKey, pendingPolicyName, toast]
  );

  const handleCloseEvaluateModal = useCallback(() => {
    setIsEvaluateModalOpen(false);
    setEvaluateResults(null);
    setEvaluatingPolicyName(undefined);
  }, []);

  const antTableConfig = useMemo(
    () => ({
      dataSource,
      totalRows,
      isLoading,
      isFetching,
      getRowKey: (record: (typeof dataSource)[number]) => record.id,
      customTableProps: {
        locale: {
          emptyText: <EmptyTableNotice />,
        },
      },
    }),
    [totalRows, isLoading, isFetching, dataSource],
  );

  const { tableProps } = useAntTable(tableState, antTableConfig);

  const columns: ColumnsType<(typeof dataSource)[number]> = useMemo(
    () => [
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        render: (_, { fides_key, name }) => (
          <LinkCell
            href={`${POLICIES_V2_ROUTE}/${fides_key}`}
            data-testid="policy-name"
          >
            {name}
          </LinkCell>
        ),
      },
      {
        title: "Fides Key",
        dataIndex: "fides_key",
        key: "fides_key",
        render: (_, { fides_key }) => (
          <Tag color="default" data-testid="policy-key">
            {fides_key}
          </Tag>
        ),
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        ellipsis: true,
        render: (_, { description }) => description || "-",
      },
      {
        title: "Rules",
        dataIndex: "ruleCount",
        key: "ruleCount",
        width: 80,
        render: (_, { ruleCount }) => (
          <Tag color="info" data-testid="rule-count">
            {ruleCount}
          </Tag>
        ),
      },
      {
        title: "Status",
        dataIndex: "enabled",
        key: "enabled",
        width: 100,
        render: (_, { enabled }) => (
          <Tag
            color={enabled ? "success" : "default"}
            data-testid="status-badge"
          >
            {enabled ? "Enabled" : "Disabled"}
          </Tag>
        ),
      },
      ...(userCanUpdate
        ? [
            {
              title: "Enable",
              dataIndex: "toggle",
              key: "toggle",
              width: 80,
              render: (_: unknown, record: (typeof dataSource)[number]) => (
                <Switch
                  checked={record.enabled}
                  onChange={() => handleToggleEnabled(record)}
                  data-testid="enable-toggle"
                />
              ),
              onCell: () => ({
                onClick: (e: React.MouseEvent) => e.stopPropagation(),
              }),
            },
          ]
        : []),
      ...(userCanDelete || userCanEvaluate
        ? [
            {
              title: "Actions",
              key: "actions",
              width: 140,
              render: (_: unknown, record: (typeof dataSource)[number]) => (
                <Flex gap="small">
                  {userCanEvaluate && record.enabled && (
                    <Tooltip title="Evaluate this policy against all systems">
                      <Button
                        type="text"
                        icon={<Icons.Activity />}
                        onClick={() =>
                          handleEvaluateSinglePolicy(
                            record.fides_key,
                            record.name
                          )
                        }
                        data-testid="evaluate-btn"
                      />
                    </Tooltip>
                  )}
                  {userCanDelete && (
                    <Button
                      type="text"
                      danger
                      icon={<Icons.TrashCan />}
                      onClick={() => handleDelete(record.fides_key)}
                      data-testid="delete-btn"
                    />
                  )}
                </Flex>
              ),
              onCell: () => ({
                onClick: (e: React.MouseEvent) => e.stopPropagation(),
              }),
            },
          ]
        : []),
    ],
    [userCanUpdate, userCanDelete, userCanEvaluate, handleEvaluateSinglePolicy],
  );

  return {
    tableProps,
    columns,
    userCanUpdate,
    userCanDelete,
    userCanEvaluate,
    isEmpty: !isLoading && items.length === 0,
    // Options modal state and handlers
    isOptionsModalOpen,
    pendingPolicyName,
    handleEvaluateAllPolicies,
    handleCloseOptionsModal,
    handleRunEvaluation,
    // Evaluate results modal state and handlers
    isEvaluateModalOpen,
    evaluateResults,
    evaluatingPolicyName,
    isEvaluating,
    handleCloseEvaluateModal,
  };
};

export default usePolicyV2Table;
