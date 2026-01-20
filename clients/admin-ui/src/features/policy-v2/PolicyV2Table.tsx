import { Button, Flex, Icons, Table } from "fidesui";
import { useRouter } from "next/router";
import { useCallback, useState } from "react";

import { POLICIES_V2_ROUTE } from "~/features/common/nav/routes";
import { EvaluateOptionsModal } from "~/features/policy-v2/EvaluateOptionsModal";
import { EvaluateResultsModal } from "~/features/policy-v2/EvaluateResultsModal";
import { PolicyV2ChatModal } from "~/features/policy-v2/PolicyV2ChatModal";
import usePolicyV2Table from "~/features/policy-v2/usePolicyV2Table";
import { PolicyV2Create } from "~/features/policy-v2/types";

export const PolicyV2Table = () => {
  const {
    tableProps,
    columns,
    userCanUpdate,
    userCanEvaluate,
    // Options modal
    isOptionsModalOpen,
    pendingPolicyName,
    handleEvaluateAllPolicies,
    handleCloseOptionsModal,
    handleRunEvaluation,
    // Results modal
    isEvaluateModalOpen,
    evaluateResults,
    evaluatingPolicyName,
    isEvaluating,
    handleCloseEvaluateModal,
  } = usePolicyV2Table();

  const router = useRouter();
  const [isChatModalOpen, setIsChatModalOpen] = useState(false);

  const handlePolicyGenerated = useCallback(
    (policy: PolicyV2Create) => {
      router.push({
        pathname: `${POLICIES_V2_ROUTE}/new`,
        query: { prefill: JSON.stringify(policy) },
      });
    },
    [router]
  );

  return (
    <Flex vertical gap="middle" style={{ width: "100%" }}>
      <Flex justify="space-between">
        <Flex gap="small">
          {userCanEvaluate && (
            <Button
              onClick={handleEvaluateAllPolicies}
              icon={<Icons.Activity />}
              data-testid="evaluate-all-btn"
            >
              Evaluate All Policies
            </Button>
          )}
        </Flex>
        <Flex gap="small">
          {userCanUpdate && (
            <>
              <Button
                onClick={() => setIsChatModalOpen(true)}
                icon={<Icons.AiGenerate />}
                data-testid="create-with-ai-btn"
              >
                Create with AI
              </Button>
              <Button
                onClick={() => router.push(`${POLICIES_V2_ROUTE}/new`)}
                type="primary"
                data-testid="add-policy-v2-btn"
              >
                Add a policy +
              </Button>
            </>
          )}
        </Flex>
      </Flex>
      <Table {...tableProps} columns={columns} />

      <EvaluateOptionsModal
        isOpen={isOptionsModalOpen}
        onClose={handleCloseOptionsModal}
        onEvaluate={handleRunEvaluation}
        policyName={pendingPolicyName}
        isLoading={isEvaluating}
      />

      <EvaluateResultsModal
        isOpen={isEvaluateModalOpen}
        onClose={handleCloseEvaluateModal}
        isLoading={isEvaluating}
        results={evaluateResults}
        policyName={evaluatingPolicyName}
      />

      <PolicyV2ChatModal
        isOpen={isChatModalOpen}
        onClose={() => setIsChatModalOpen(false)}
        onPolicyGenerated={handlePolicyGenerated}
      />
    </Flex>
  );
};
