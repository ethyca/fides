import React, { useCallback, useEffect, useState, useMemo } from "react";
import {
  Button,
  ChakraAlert as Alert,
  ChakraAlertDescription as AlertDescription,
  ChakraAlertIcon as AlertIcon,
  ChakraBox as Box,
  ChakraFlex as Flex,
  ChakraText as Text,
  Icons,
  useChakraToast as useToast,
} from "fidesui";

import FidesSpinner from "~/features/common/FidesSpinner";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { errorToastParams, successToastParams } from "~/features/common/toast";

import {
  useUpdatePolicyV2Mutation,
  useCreatePolicyV2Mutation,
} from "../policy-v2.slice";
import {
  PolicyV2,
  PolicyV2Create,
  PolicyV2RuleConstraint,
  PolicyV2RuleMatch,
} from "../types";
import { FlowCanvas } from "./FlowCanvas";
import { useFlowToPolicy, usePolicyToFlow } from "./hooks";
import { PropertyPanel } from "./PropertyPanel";
import { SidePanel, SidePanelMode } from "./SidePanel";
import {
  ActionNodeData,
  ConstraintNodeData,
  FlowEdge,
  FlowNode,
  FlowNodeData,
  FlowNodeType,
  MatchNodeData,
  StartNodeData,
} from "./types";
import styles from "./PolicyFlowBuilder.module.scss";

interface PolicyFlowBuilderProps {
  policy: PolicyV2 | null | undefined;
  isLoading?: boolean;
  error?: string;
  /** Called after a new policy is successfully created (for navigation) */
  onPolicyCreated?: (fidesKey: string) => void;
}

export const PolicyFlowBuilder = ({
  policy,
  isLoading,
  error,
  onPolicyCreated,
}: PolicyFlowBuilderProps) => {
  // Get initial nodes and edges from the policy
  const { nodes: initialNodes, edges: initialEdges } = usePolicyToFlow(policy);

  // Lift state from usePolicyToFlow to enable local updates
  const [nodes, setNodes] = useState<FlowNode[]>(initialNodes);
  const [edges, setEdges] = useState<FlowEdge[]>(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [isDirty, setIsDirty] = useState<boolean>(false);

  // Side panel mode and AI policy state
  const [sidePanelMode, setSidePanelMode] = useState<SidePanelMode>("nodes");
  const [aiPolicy, setAiPolicy] = useState<PolicyV2Create | null>(null);
  const [isUpdatingFlow, setIsUpdatingFlow] = useState(false);

  // Progressive reveal state for AI-generated flows
  const [revealedNodeCount, setRevealedNodeCount] = useState(0);
  const [isRevealing, setIsRevealing] = useState(false);

  // Convert AI policy to flow nodes/edges
  const aiFlowResult = usePolicyToFlow(
    aiPolicy
      ? {
          ...aiPolicy,
          id: "ai-generated",
          enabled: true,
        }
      : null
  );

  // Progressive reveal effect - animate nodes appearing one by one
  useEffect(() => {
    if (!aiPolicy || aiFlowResult.nodes.length === 0) {
      setRevealedNodeCount(0);
      setIsRevealing(false);
      return;
    }

    // Start progressive reveal
    setIsRevealing(true);
    setRevealedNodeCount(0);

    const totalNodes = aiFlowResult.nodes.length;
    let currentCount = 0;

    // Reveal nodes one by one with a delay
    const revealInterval = setInterval(() => {
      currentCount += 1;
      setRevealedNodeCount(currentCount);

      if (currentCount >= totalNodes) {
        clearInterval(revealInterval);
        // Short delay before marking as complete
        setTimeout(() => {
          setIsRevealing(false);
          setIsUpdatingFlow(false);
        }, 300);
      }
    }, 150); // 150ms delay between each node

    return () => {
      clearInterval(revealInterval);
    };
  }, [aiPolicy, aiFlowResult.nodes.length]);

  // Determine which nodes/edges to display based on mode
  const displayNodes = useMemo(() => {
    if (sidePanelMode === "chat" && aiPolicy) {
      // During progressive reveal, only show revealed nodes
      if (isRevealing) {
        return aiFlowResult.nodes.slice(0, revealedNodeCount);
      }
      return aiFlowResult.nodes;
    }
    return nodes;
  }, [sidePanelMode, aiPolicy, aiFlowResult.nodes, nodes, isRevealing, revealedNodeCount]);

  const displayEdges = useMemo(() => {
    if (sidePanelMode === "chat" && aiPolicy) {
      // During progressive reveal, only show edges for revealed nodes
      if (isRevealing) {
        const revealedNodeIds = new Set(
          aiFlowResult.nodes.slice(0, revealedNodeCount).map((n) => n.id)
        );
        return aiFlowResult.edges.filter(
          (e) => revealedNodeIds.has(e.source) && revealedNodeIds.has(e.target)
        );
      }
      return aiFlowResult.edges;
    }
    return edges;
  }, [sidePanelMode, aiPolicy, aiFlowResult.nodes, aiFlowResult.edges, edges, isRevealing, revealedNodeCount]);

  // Calculate reveal progress percentage
  const revealProgress = useMemo(() => {
    if (!isRevealing || aiFlowResult.nodes.length === 0) return 0;
    return Math.round((revealedNodeCount / aiFlowResult.nodes.length) * 100);
  }, [isRevealing, revealedNodeCount, aiFlowResult.nodes.length]);

  // Hooks for save functionality
  const toast = useToast();
  const [updatePolicy, { isLoading: isSaving }] = useUpdatePolicyV2Mutation();
  const [createPolicy, { isLoading: isCreating }] = useCreatePolicyV2Mutation();
  const { rules, isValid, errors } = useFlowToPolicy({ nodes, edges });

  // Update local state when policy changes
  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
    setIsDirty(false);
  }, [initialNodes, initialEdges]);

  // Warn user about unsaved changes when leaving page
  useEffect(() => {
    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      if (isDirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };

    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => {
      window.removeEventListener("beforeunload", handleBeforeUnload);
    };
  }, [isDirty]);

  // Find the selected node from the displayed nodes array (handles both regular and AI-generated nodes)
  const selectedNode = selectedNodeId
    ? displayNodes.find((node) => node.id === selectedNodeId) || null
    : null;

  // Handle saving the policy
  const handleSave = useCallback(async () => {
    if (!policy) {
      return;
    }

    // Show validation errors if any
    if (!isValid) {
      const errorMessages = errors.map((err) => `${err.ruleName}: ${err.message}`);
      toast(
        errorToastParams(
          <>
            <div>Cannot save policy due to validation errors:</div>
            <ul style={{ marginLeft: "1.5em", marginTop: "0.5em" }}>
              {errorMessages.map((msg, idx) => (
                <li key={idx}>{msg}</li>
              ))}
            </ul>
          </>
        )
      );
      return;
    }

    try {
      const result = await updatePolicy({
        fides_key: policy.fides_key,
        rules,
      });

      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
      } else {
        toast(successToastParams("Policy updated successfully"));
        setIsDirty(false);
      }
    } catch (err) {
      toast(errorToastParams("Failed to save policy"));
    }
  }, [policy, isValid, errors, rules, updatePolicy, toast]);

  // Handle node updates from PropertyPanel
  const handleNodeUpdate = useCallback(
    (nodeId: string, updatedData: FlowNodeData) => {
      setNodes((prevNodes) =>
        prevNodes.map((node) =>
          node.id === nodeId ? { ...node, data: updatedData } : node,
        ),
      );
      setIsDirty(true);
    },
    [],
  );

  // Handle closing the property panel
  const handleClosePanel = useCallback(() => {
    setSelectedNodeId(null);
  }, []);

  // Generate unique ID for new nodes
  const generateNodeId = useCallback(() => {
    return `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // Handle adding a new rule
  const handleAddRule = useCallback(() => {
    if (!policy) {
      return;
    }

    // Find the maximum yOffset to position the new rule below existing ones
    const maxY = nodes.reduce((max, node) => Math.max(max, node.position.y), 0);
    const newRuleY = maxY + 300; // Space rules vertically

    const newRuleId = `rule-${Date.now()}`;
    const startNodeId = generateNodeId();
    const actionNodeId = generateNodeId();

    // Create start node
    const startNode: FlowNode = {
      id: startNodeId,
      type: "start",
      position: { x: 100, y: newRuleY },
      data: {
        nodeType: "start",
        ruleId: newRuleId,
        ruleName: "New Rule",
      } as StartNodeData,
    };

    // Create action node
    const actionNode: FlowNode = {
      id: actionNodeId,
      type: "action",
      position: { x: 700, y: newRuleY },
      data: {
        nodeType: "action",
        ruleId: newRuleId,
        action: "ALLOW",
        onDenialMessage: null,
      } as ActionNodeData,
    };

    // Create edge from start to action
    const edge: FlowEdge = {
      id: `${startNodeId}-${actionNodeId}`,
      source: startNodeId,
      target: actionNodeId,
      type: "default",
    };

    setNodes((prevNodes) => [...prevNodes, startNode, actionNode]);
    setEdges((prevEdges) => [...prevEdges, edge]);
    setIsDirty(true);
  }, [policy, nodes, generateNodeId]);

  // Handle dropping a node from the palette
  const handleDrop = useCallback(
    (nodeType: FlowNodeType, position: { x: number; y: number }) => {
      if (!policy || !policy.rules || policy.rules.length === 0) {
        return;
      }

      // For now, associate with the first rule
      const firstRule = policy.rules[0];
      const ruleId = firstRule.name || "rule-0";
      const nodeId = generateNodeId();

      let newNode: FlowNode;

      switch (nodeType) {
        case "match":
          newNode = {
            id: nodeId,
            type: "match",
            position,
            data: {
              nodeType: "match",
              ruleId,
              matchIndex: 0,
              match: {
                match_type: "key",
                target_field: "data_category",
                operator: "any",
                values: [],
              } as PolicyV2RuleMatch,
            } as MatchNodeData,
          };
          break;

        case "constraint":
          newNode = {
            id: nodeId,
            type: "constraint",
            position,
            data: {
              nodeType: "constraint",
              ruleId,
              constraintIndex: 0,
              constraint: {
                constraint_type: "privacy",
                configuration: {
                  privacy_notice_key: "",
                  requirement: "not_opt_out",
                },
              } as PolicyV2RuleConstraint,
            } as ConstraintNodeData,
          };
          break;

        case "action":
          newNode = {
            id: nodeId,
            type: "action",
            position,
            data: {
              nodeType: "action",
              ruleId,
              action: "ALLOW",
              onDenialMessage: null,
            } as ActionNodeData,
          };
          break;

        default:
          return;
      }

      setNodes((prevNodes) => [...prevNodes, newNode]);
      setIsDirty(true);
    },
    [policy, generateNodeId],
  );

  // Handle AI policy generation
  const handleAIPolicyGenerated = useCallback((generatedPolicy: PolicyV2Create) => {
    setIsUpdatingFlow(true);
    setAiPolicy(generatedPolicy);
    // Progressive reveal will handle clearing isUpdatingFlow
  }, []);

  // Handle saving AI-generated policy
  const handleAIPolicySave = useCallback(
    async (policyToSave: PolicyV2Create) => {
      try {
        const result = await createPolicy(policyToSave);

        if (isErrorResult(result)) {
          toast(errorToastParams(getErrorMessage(result.error)));
        } else {
          toast(successToastParams(`Policy "${policyToSave.name}" created successfully`));
          // Navigate to the new policy if callback provided
          // Don't clear AI policy state - let navigation handle the transition
          // This keeps the flow visible until the new page loads
          if (onPolicyCreated) {
            onPolicyCreated(policyToSave.fides_key);
          }
          // Only clear state if we're NOT navigating away
          // (i.e., when used in a context without navigation callback)
          if (!onPolicyCreated) {
            setAiPolicy(null);
            setSidePanelMode("nodes");
          }
        }
      } catch (err) {
        toast(errorToastParams("Failed to create policy"));
      }
    },
    [createPolicy, toast, onPolicyCreated]
  );

  // Handle side panel mode change
  const handleModeChange = useCallback(
    (mode: SidePanelMode) => {
      // If switching from chat mode with an AI policy to nodes mode, confirm
      if (sidePanelMode === "chat" && mode === "nodes" && aiPolicy) {
        // Just switch - the AI policy preview remains in the chat pane
      }
      setSidePanelMode(mode);
    },
    [sidePanelMode, aiPolicy]
  );

  // Show loading state
  if (isLoading) {
    return (
      <Box className={styles.container}>
        <Flex className={styles.loadingContainer}>
          <FidesSpinner />
        </Flex>
      </Box>
    );
  }

  // Show error state
  if (error) {
    return (
      <Box className={styles.container}>
        <Flex className={styles.errorContainer}>
          <Alert status="error" borderRadius="md">
            <AlertIcon />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        </Flex>
      </Box>
    );
  }

  // Show empty state if no policy or no rules (but with AI chat available)
  if (!policy || !policy.rules || policy.rules.length === 0) {
    // If we have an AI-generated policy, show it
    const showAiFlow = sidePanelMode === "chat" && aiPolicy;

    return (
      <Box className={styles.container}>
        <Flex className={styles.header}>
          <Flex flex="1" align="center" gap={4}>
            <Text className={styles.policyName}>
              {showAiFlow ? aiPolicy.name : "New Policy"}
            </Text>
            {showAiFlow && (
              <Text className={styles.ruleCount}>
                {aiPolicy.rules?.length || 0}{" "}
                {(aiPolicy.rules?.length || 0) === 1 ? "rule" : "rules"} (AI Generated)
              </Text>
            )}
          </Flex>
        </Flex>
        <Flex className={styles.contentWrapper}>
          <SidePanel
            mode={sidePanelMode}
            onModeChange={handleModeChange}
            onAddRule={handleAddRule}
            onAIPolicyGenerated={handleAIPolicyGenerated}
            onAIPolicySave={handleAIPolicySave}
            aiPolicy={aiPolicy}
            isUpdatingFlow={isUpdatingFlow}
            isRevealing={isRevealing}
            revealProgress={revealProgress}
            hasExistingPolicy={false}
          />
          <Box flex="1" className={styles.canvasWrapper}>
            {showAiFlow ? (
              <FlowCanvas
                initialNodes={displayNodes}
                initialEdges={displayEdges}
                onNodeSelect={setSelectedNodeId}
                onDrop={handleDrop}
                readOnly
              />
            ) : (
              <Flex className={styles.emptyContainer}>
                <Box textAlign="center">
                  <Text fontSize="lg" fontWeight="semibold" color="gray.700" mb={2}>
                    No rules to display
                  </Text>
                  <Text fontSize="sm" color="gray.500" mb={4}>
                    Add rules to this policy to visualize the flow
                  </Text>
                  <Text fontSize="sm" color="gray.500">
                    Or use the AI Chat tab to create a policy with AI assistance
                  </Text>
                </Box>
              </Flex>
            )}
          </Box>
          <PropertyPanel
            selectedNode={selectedNode}
            onNodeUpdate={handleNodeUpdate}
            onClose={handleClosePanel}
          />
        </Flex>
      </Box>
    );
  }

  // Determine if showing AI-generated preview
  const isShowingAiPreview = sidePanelMode === "chat" && aiPolicy;
  const displayPolicyName = isShowingAiPreview ? aiPolicy.name : policy.name;
  const displayRuleCount = isShowingAiPreview
    ? aiPolicy.rules?.length || 0
    : policy.rules.length;

  return (
    <Box className={styles.container}>
      <Flex className={styles.header}>
        <Flex flex="1" align="center" gap={4}>
          <Text className={styles.policyName}>{displayPolicyName}</Text>
          <Text className={styles.ruleCount}>
            {displayRuleCount} {displayRuleCount === 1 ? "rule" : "rules"}
            {isShowingAiPreview && " (AI Preview)"}
          </Text>
          {isDirty && !isShowingAiPreview && (
            <Text color="orange.600" fontSize="sm" fontWeight="medium">
              (unsaved changes)
            </Text>
          )}
        </Flex>
        {isDirty && (
          <Flex gap={2}>
            <Button
              type="primary"
              icon={<Icons.Save />}
              onClick={handleSave}
              loading={isSaving}
              disabled={!isValid}
            >
              Save Changes
            </Button>
            {!isValid && errors.length > 0 && (
              <Alert status="warning" variant="subtle" size="sm">
                <AlertIcon />
                <AlertDescription fontSize="sm">
                  {errors.length} validation {errors.length === 1 ? "error" : "errors"}
                </AlertDescription>
              </Alert>
            )}
          </Flex>
        )}
      </Flex>
      <Flex className={styles.contentWrapper}>
        <SidePanel
          mode={sidePanelMode}
          onModeChange={handleModeChange}
          onAddRule={handleAddRule}
          onAIPolicyGenerated={handleAIPolicyGenerated}
          onAIPolicySave={handleAIPolicySave}
          aiPolicy={aiPolicy}
          isUpdatingFlow={isUpdatingFlow}
          isRevealing={isRevealing}
          revealProgress={revealProgress}
          hasExistingPolicy={!!policy}
        />
        <Box flex="1" className={styles.canvasWrapper}>
          <FlowCanvas
            initialNodes={displayNodes}
            initialEdges={displayEdges}
            onNodeSelect={setSelectedNodeId}
            onDrop={handleDrop}
            readOnly={sidePanelMode === "chat"}
          />
        </Box>
        <PropertyPanel
          selectedNode={selectedNode}
          onNodeUpdate={handleNodeUpdate}
          onClose={handleClosePanel}
        />
      </Flex>
    </Box>
  );
};
