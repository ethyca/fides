import {
  Button,
  ChakraBox as Box,
  ChakraCloseIcon as CloseIcon,
  ChakraStack as Stack,
  ChakraText as Text,
  Flex,
  Input,
  Select,
  Space,
  Tag,
  Typography,
} from "fidesui";
import { useState } from "react";

import {
  PolicyV2Action,
  PolicyV2RuleConstraint,
  PolicyV2RuleMatch,
  PrivacyConstraintConfig,
  ContextConstraintConfig,
} from "../types";
import {
  FlowNode,
  FlowNodeData,
  StartNodeData,
  MatchNodeData,
  GateNodeData,
  ConstraintNodeData,
  ActionNodeData,
} from "./types";
import styles from "./PropertyPanel.module.scss";

const { Title } = Typography;

interface PropertyPanelProps {
  selectedNode: FlowNode | null;
  onNodeUpdate: (nodeId: string, data: FlowNodeData) => void;
  onClose: () => void;
}

const MATCH_TYPE_OPTIONS = [
  { value: "key", label: "Key Match" },
  { value: "taxonomy", label: "Taxonomy Match" },
];

const TARGET_FIELD_OPTIONS = [
  { value: "data_category", label: "Data Category" },
  { value: "data_use", label: "Data Use" },
  { value: "data_subject", label: "Data Subject" },
  { value: "data_use_taxonomies", label: "Data Use Taxonomies" },
  { value: "data_category_taxonomies", label: "Data Category Taxonomies" },
];

const OPERATOR_OPTIONS = [
  { value: "any", label: "Any (OR)" },
  { value: "all", label: "All (AND)" },
];

const CONSTRAINT_TYPE_OPTIONS = [
  { value: "privacy", label: "Privacy Constraint" },
  { value: "context", label: "Context Constraint" },
];

const CONSENT_REQUIREMENT_OPTIONS = [
  { value: "opt_in", label: "Opt In" },
  { value: "not_opt_out", label: "Not Opt Out" },
];

const ACTION_OPTIONS = [
  { value: "ALLOW", label: "Allow" },
  { value: "DENY", label: "Deny" },
];

const getNodeTypeTitle = (nodeType: FlowNodeData["nodeType"]): string => {
  switch (nodeType) {
    case "start":
      return "Start Node";
    case "match":
      return "Match Condition";
    case "gate":
      return "Gate (AND)";
    case "constraint":
      return "Constraint";
    case "action":
      return "Action";
    default:
      return "Node Properties";
  }
};

const StartNodePanel = ({ data }: { data: StartNodeData }) => (
  <Stack spacing={4}>
    <div>
      <Text fontSize="sm" color="gray.600" mb={1}>
        Rule Name
      </Text>
      <Text fontSize="md" fontWeight="medium">
        {data.ruleName}
      </Text>
    </div>
    <Text fontSize="sm" color="gray.500" fontStyle="italic">
      This is the starting point for the rule. It cannot be edited.
    </Text>
  </Stack>
);

const MatchNodePanel = ({
  data,
  onUpdate,
}: {
  data: MatchNodeData;
  onUpdate: (data: MatchNodeData) => void;
}) => {
  const [newValue, setNewValue] = useState("");

  const handleMatchChange = (updates: Partial<PolicyV2RuleMatch>) => {
    onUpdate({
      ...data,
      match: {
        ...data.match,
        ...updates,
      },
    });
  };

  const handleAddValue = () => {
    if (newValue.trim()) {
      handleMatchChange({
        values: [...data.match.values, newValue.trim()],
      });
      setNewValue("");
    }
  };

  const handleRemoveValue = (index: number) => {
    handleMatchChange({
      values: data.match.values.filter((_, i) => i !== index),
    });
  };

  return (
    <Stack spacing={4}>
      <div>
        <Text fontSize="sm" color="gray.600" mb={1}>
          Match Type
        </Text>
        <Select
          value={data.match.match_type}
          onChange={(value) =>
            handleMatchChange({ match_type: value as "key" | "taxonomy" })
          }
          options={MATCH_TYPE_OPTIONS}
          style={{ width: "100%" }}
        />
      </div>

      <div>
        <Text fontSize="sm" color="gray.600" mb={1}>
          Target Field
        </Text>
        <Select
          value={data.match.target_field}
          onChange={(value) => handleMatchChange({ target_field: value })}
          options={TARGET_FIELD_OPTIONS}
          style={{ width: "100%" }}
        />
      </div>

      <div>
        <Text fontSize="sm" color="gray.600" mb={1}>
          Operator
        </Text>
        <Select
          value={data.match.operator}
          onChange={(value) =>
            handleMatchChange({ operator: value as "any" | "all" })
          }
          options={OPERATOR_OPTIONS}
          style={{ width: "100%" }}
        />
      </div>

      <div>
        <Text fontSize="sm" color="gray.600" mb={1}>
          Values
        </Text>
        <Space wrap size={4} style={{ marginBottom: 8 }}>
          {data.match.values.map((value, index) => (
            <Tag
              key={index}
              closable
              onClose={() => handleRemoveValue(index)}
              style={{ marginBottom: 4 }}
            >
              {typeof value === "string"
                ? value
                : `${value.taxonomy}:${value.element}`}
            </Tag>
          ))}
        </Space>
        <Flex gap={8}>
          <Input
            placeholder="Add value (e.g., marketing.advertising)"
            value={newValue}
            onChange={(e) => setNewValue(e.target.value)}
            onPressEnter={handleAddValue}
            size="small"
          />
          <Button onClick={handleAddValue} size="small">
            Add
          </Button>
        </Flex>
      </div>
    </Stack>
  );
};

const GateNodePanel = ({ data }: { data: GateNodeData }) => (
  <Stack spacing={4}>
    <div>
      <Text fontSize="sm" color="gray.600" mb={1}>
        Gate Type
      </Text>
      <Text fontSize="md" fontWeight="medium">
        AND
      </Text>
    </div>
    <Text fontSize="sm" color="gray.500" fontStyle="italic">
      This gate ensures all preceding match conditions are satisfied. It is
      auto-generated and cannot be edited.
    </Text>
  </Stack>
);

const ConstraintNodePanel = ({
  data,
  onUpdate,
}: {
  data: ConstraintNodeData;
  onUpdate: (data: ConstraintNodeData) => void;
}) => {
  const handleConstraintChange = (
    updates: Partial<PolicyV2RuleConstraint>,
  ) => {
    onUpdate({
      ...data,
      constraint: {
        ...data.constraint,
        ...updates,
      },
    });
  };

  const isPrivacyConstraint = data.constraint.constraint_type === "privacy";
  const config = data.constraint.configuration as
    | PrivacyConstraintConfig
    | ContextConstraintConfig;

  return (
    <Stack spacing={4}>
      <div>
        <Text fontSize="sm" color="gray.600" mb={1}>
          Constraint Type
        </Text>
        <Select
          value={data.constraint.constraint_type}
          onChange={(value) => {
            const newConfig =
              value === "privacy"
                ? { privacy_notice_key: "", requirement: "not_opt_out" as const }
                : { field: "", operator: "equals", values: [] };
            handleConstraintChange({
              constraint_type: value as "privacy" | "context",
              configuration: newConfig,
            });
          }}
          options={CONSTRAINT_TYPE_OPTIONS}
          style={{ width: "100%" }}
        />
      </div>

      {isPrivacyConstraint ? (
        <>
          <div>
            <Text fontSize="sm" color="gray.600" mb={1}>
              Privacy Notice Key
            </Text>
            <Input
              placeholder="Enter privacy notice key"
              value={(config as PrivacyConstraintConfig).privacy_notice_key || ""}
              onChange={(e) =>
                handleConstraintChange({
                  configuration: {
                    ...config,
                    privacy_notice_key: e.target.value,
                  },
                })
              }
            />
          </div>

          <div>
            <Text fontSize="sm" color="gray.600" mb={1}>
              Requirement
            </Text>
            <Select
              value={(config as PrivacyConstraintConfig).requirement || "not_opt_out"}
              onChange={(value) =>
                handleConstraintChange({
                  configuration: {
                    ...config,
                    requirement: value as "opt_in" | "not_opt_out",
                  },
                })
              }
              options={CONSENT_REQUIREMENT_OPTIONS}
              style={{ width: "100%" }}
            />
          </div>
        </>
      ) : (
        <>
          <div>
            <Text fontSize="sm" color="gray.600" mb={1}>
              Context Field
            </Text>
            <Input
              placeholder="Enter context field (e.g., geo_location)"
              value={(config as ContextConstraintConfig).field || ""}
              onChange={(e) =>
                handleConstraintChange({
                  configuration: {
                    ...config,
                    field: e.target.value,
                  },
                })
              }
            />
          </div>

          <div>
            <Text fontSize="sm" color="gray.600" mb={1}>
              Operator
            </Text>
            <Input
              placeholder="Enter operator (e.g., equals, contains)"
              value={(config as ContextConstraintConfig).operator || ""}
              onChange={(e) =>
                handleConstraintChange({
                  configuration: {
                    ...config,
                    operator: e.target.value,
                  },
                })
              }
            />
          </div>

          <div>
            <Text fontSize="sm" color="gray.600" mb={1}>
              Values
            </Text>
            <Input
              placeholder="Comma-separated values"
              value={
                (config as ContextConstraintConfig).values
                  ? (config as ContextConstraintConfig).values.join(", ")
                  : ""
              }
              onChange={(e) =>
                handleConstraintChange({
                  configuration: {
                    ...config,
                    values: e.target.value
                      .split(",")
                      .map((v) => v.trim())
                      .filter((v) => v),
                  },
                })
              }
            />
          </div>
        </>
      )}
    </Stack>
  );
};

const ActionNodePanel = ({
  data,
  onUpdate,
}: {
  data: ActionNodeData;
  onUpdate: (data: ActionNodeData) => void;
}) => (
  <Stack spacing={4}>
    <div>
      <Text fontSize="sm" color="gray.600" mb={1}>
        Action
      </Text>
      <Select
        value={data.action}
        onChange={(value) =>
          onUpdate({
            ...data,
            action: value as PolicyV2Action,
          })
        }
        options={ACTION_OPTIONS}
        style={{ width: "100%" }}
      />
    </div>

    {data.action === "DENY" && (
      <div>
        <Text fontSize="sm" color="gray.600" mb={1}>
          On Denial Message (Optional)
        </Text>
        <Input.TextArea
          placeholder="Message to display when this action denies access"
          value={data.onDenialMessage || ""}
          onChange={(e) =>
            onUpdate({
              ...data,
              onDenialMessage: e.target.value,
            })
          }
          rows={3}
        />
      </div>
    )}

    <Text fontSize="sm" color="gray.500" fontStyle="italic">
      {data.action === "ALLOW"
        ? "This action will allow access when all conditions are met."
        : "This action will deny access when all conditions are met."}
    </Text>
  </Stack>
);

export const PropertyPanel: React.FC<PropertyPanelProps> = ({
  selectedNode,
  onNodeUpdate,
  onClose,
}) => {
  if (!selectedNode) {
    return null;
  }

  const handleUpdate = (updatedData: FlowNodeData) => {
    onNodeUpdate(selectedNode.id, updatedData);
  };

  const renderContent = () => {
    switch (selectedNode.data.nodeType) {
      case "start":
        return <StartNodePanel data={selectedNode.data as StartNodeData} />;
      case "match":
        return (
          <MatchNodePanel
            data={selectedNode.data as MatchNodeData}
            onUpdate={handleUpdate}
          />
        );
      case "gate":
        return <GateNodePanel data={selectedNode.data as GateNodeData} />;
      case "constraint":
        return (
          <ConstraintNodePanel
            data={selectedNode.data as ConstraintNodeData}
            onUpdate={handleUpdate}
          />
        );
      case "action":
        return (
          <ActionNodePanel
            data={selectedNode.data as ActionNodeData}
            onUpdate={handleUpdate}
          />
        );
      default:
        return null;
    }
  };

  return (
    <Box className={styles.panel}>
      <Box className={styles.header}>
        <Flex justify="space-between" align="center">
          <Title level={4} style={{ margin: 0 }}>
            {getNodeTypeTitle(selectedNode.data.nodeType)}
          </Title>
          <Button
            aria-label="Close property panel"
            onClick={onClose}
            icon={<CloseIcon fontSize="smaller" />}
            data-testid="close-property-panel"
          />
        </Flex>
      </Box>

      <Box className={styles.content}>{renderContent()}</Box>
    </Box>
  );
};
