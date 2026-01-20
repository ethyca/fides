import {
  Button,
  Card,
  ChakraBox as Box,
  ChakraStack as Stack,
  ChakraVStack as VStack,
  Flex,
  Icons,
  Input,
  Select,
  Space,
  Tag,
  Typography,
  useChakraToast as useToast,
} from "fidesui";
import { Form, Formik } from "formik";
import { useRouter } from "next/router";
import { useMemo, useState } from "react";
import * as Yup from "yup";

import FormSection from "~/features/common/form/FormSection";
import {
  CustomSwitch,
  CustomTextArea,
  CustomTextInput,
} from "~/features/common/form/inputs";
import { getErrorMessage, isErrorResult } from "~/features/common/helpers";
import { POLICIES_V2_ROUTE } from "~/features/common/nav/routes";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useCreatePolicyV2Mutation,
  useUpdatePolicyV2Mutation,
} from "~/features/policy-v2/policy-v2.slice";
import {
  PolicyV2,
  PolicyV2Create,
  PolicyV2Rule,
  PolicyV2RuleMatch,
  PolicyV2RuleConstraint,
} from "~/features/policy-v2/types";

const { Text, Title } = Typography;

const ACTION_OPTIONS = [
  { value: "ALLOW", label: "Allow" },
  { value: "DENY", label: "Deny" },
];

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

const ValidationSchema = Yup.object().shape({
  fides_key: Yup.string()
    .required("Fides key is required")
    .matches(
      /^[a-z0-9_]+$/,
      "Fides key must contain only lowercase letters, numbers, and underscores",
    ),
  name: Yup.string().required("Name is required"),
});

interface FormValues {
  fides_key: string;
  name: string;
  description: string;
  enabled: boolean;
  rules: PolicyV2Rule[];
}

const defaultMatch: Omit<PolicyV2RuleMatch, "id"> = {
  match_type: "key",
  target_field: "data_use",
  operator: "any",
  values: [],
};

const defaultConstraint: Omit<PolicyV2RuleConstraint, "id"> = {
  constraint_type: "privacy",
  configuration: {
    privacy_notice_key: "",
    requirement: "not_opt_out",
  },
};

const RuleMatchEditor = ({
  match,
  index,
  onChange,
  onRemove,
}: {
  match: PolicyV2RuleMatch;
  index: number;
  onChange: (match: PolicyV2RuleMatch) => void;
  onRemove: () => void;
}) => {
  const [newValue, setNewValue] = useState("");

  const handleAddValue = () => {
    if (newValue.trim()) {
      onChange({
        ...match,
        values: [...match.values, newValue.trim()],
      });
      setNewValue("");
    }
  };

  const handleRemoveValue = (valueIndex: number) => {
    onChange({
      ...match,
      values: match.values.filter((_, i) => i !== valueIndex),
    });
  };

  return (
    <Card size="small" style={{ marginBottom: 8 }}>
      <Flex justify="space-between" align="center" style={{ marginBottom: 8 }}>
        <Text strong>Match {index + 1}</Text>
        <Button
          type="text"
          danger
          icon={<Icons.TrashCan />}
          onClick={onRemove}
          size="small"
        />
      </Flex>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Flex gap={8}>
          <Select
            value={match.match_type}
            onChange={(value) =>
              onChange({ ...match, match_type: value as any })
            }
            options={MATCH_TYPE_OPTIONS}
            style={{ width: 150 }}
            size="small"
          />
          <Select
            value={match.target_field}
            onChange={(value) =>
              onChange({ ...match, target_field: value as any })
            }
            options={TARGET_FIELD_OPTIONS}
            style={{ width: 200 }}
            size="small"
          />
          <Select
            value={match.operator}
            onChange={(value) => onChange({ ...match, operator: value as any })}
            options={OPERATOR_OPTIONS}
            style={{ width: 120 }}
            size="small"
          />
        </Flex>
        <div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Values:
          </Text>
          <Space wrap size={4} style={{ marginTop: 4 }}>
            {match.values.map((value, valueIndex) => (
              <Tag
                key={valueIndex}
                closable
                onClose={() => handleRemoveValue(valueIndex)}
              >
                {typeof value === "string"
                  ? value
                  : `${value.taxonomy}:${value.element}`}
              </Tag>
            ))}
          </Space>
        </div>
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
      </Space>
    </Card>
  );
};

const RuleConstraintEditor = ({
  constraint,
  index,
  onChange,
  onRemove,
}: {
  constraint: PolicyV2RuleConstraint;
  index: number;
  onChange: (constraint: PolicyV2RuleConstraint) => void;
  onRemove: () => void;
}) => {
  const isPrivacyConstraint = constraint.constraint_type === "privacy";
  const config = constraint.configuration as any;

  return (
    <Card size="small" style={{ marginBottom: 8 }}>
      <Flex justify="space-between" align="center" style={{ marginBottom: 8 }}>
        <Text strong>Constraint {index + 1}</Text>
        <Button
          type="text"
          danger
          icon={<Icons.TrashCan />}
          onClick={onRemove}
          size="small"
        />
      </Flex>
      <Space direction="vertical" style={{ width: "100%" }}>
        <Select
          value={constraint.constraint_type}
          onChange={(value) =>
            onChange({
              ...constraint,
              constraint_type: value as any,
              configuration:
                value === "privacy"
                  ? { privacy_notice_key: "", requirement: "not_opt_out" }
                  : { field: "", operator: "equals", values: [] },
            })
          }
          options={CONSTRAINT_TYPE_OPTIONS}
          style={{ width: 200 }}
          size="small"
        />
        {isPrivacyConstraint ? (
          <Flex gap={8}>
            <Input
              placeholder="Privacy notice key"
              value={config.privacy_notice_key || ""}
              onChange={(e) =>
                onChange({
                  ...constraint,
                  configuration: {
                    ...config,
                    privacy_notice_key: e.target.value,
                  },
                })
              }
              size="small"
              style={{ width: 200 }}
            />
            <Select
              value={config.requirement || "not_opt_out"}
              onChange={(value) =>
                onChange({
                  ...constraint,
                  configuration: { ...config, requirement: value },
                })
              }
              options={CONSENT_REQUIREMENT_OPTIONS}
              style={{ width: 150 }}
              size="small"
            />
          </Flex>
        ) : (
          <Flex gap={8}>
            <Input
              placeholder="Context field"
              value={config.field || ""}
              onChange={(e) =>
                onChange({
                  ...constraint,
                  configuration: { ...config, field: e.target.value },
                })
              }
              size="small"
            />
          </Flex>
        )}
      </Space>
    </Card>
  );
};

const RuleEditor = ({
  rule,
  index,
  onChange,
  onRemove,
}: {
  rule: PolicyV2Rule;
  index: number;
  onChange: (rule: PolicyV2Rule) => void;
  onRemove: () => void;
}) => {
  const [isExpanded, setIsExpanded] = useState(true);

  const handleMatchChange = (matchIndex: number, match: PolicyV2RuleMatch) => {
    const newMatches = [...rule.matches];
    newMatches[matchIndex] = match;
    onChange({ ...rule, matches: newMatches });
  };

  const handleMatchRemove = (matchIndex: number) => {
    onChange({
      ...rule,
      matches: rule.matches.filter((_, i) => i !== matchIndex),
    });
  };

  const handleAddMatch = () => {
    onChange({
      ...rule,
      matches: [...rule.matches, { ...defaultMatch }],
    });
  };

  const handleConstraintChange = (
    constraintIndex: number,
    constraint: PolicyV2RuleConstraint,
  ) => {
    const newConstraints = [...rule.constraints];
    newConstraints[constraintIndex] = constraint;
    onChange({ ...rule, constraints: newConstraints });
  };

  const handleConstraintRemove = (constraintIndex: number) => {
    onChange({
      ...rule,
      constraints: rule.constraints.filter((_, i) => i !== constraintIndex),
    });
  };

  const handleAddConstraint = () => {
    onChange({
      ...rule,
      constraints: [...rule.constraints, { ...defaultConstraint }],
    });
  };

  return (
    <Card
      style={{ marginBottom: 16 }}
      styles={{
        header: {
          backgroundColor:
            rule.action === "DENY"
              ? "rgba(255, 77, 79, 0.1)"
              : "rgba(82, 196, 26, 0.1)",
        },
      }}
      title={
        <Flex justify="space-between" align="center">
          <Flex align="center" gap={8}>
            <Tag color={rule.action === "DENY" ? "error" : "success"}>
              {rule.action}
            </Tag>
            <Text strong>{rule.name || `Rule ${index + 1}`}</Text>
          </Flex>
          <Flex gap={8}>
            <Button
              type="text"
              icon={
                isExpanded ? <Icons.ChevronUp /> : <Icons.ChevronDown />
              }
              onClick={() => setIsExpanded(!isExpanded)}
              size="small"
            />
            <Button
              type="text"
              danger
              icon={<Icons.TrashCan />}
              onClick={onRemove}
              size="small"
            />
          </Flex>
        </Flex>
      }
    >
      <Box display={isExpanded ? "block" : "none"}>
        <Space direction="vertical" style={{ width: "100%" }}>
          <Flex gap={16}>
            <div style={{ flex: 1 }}>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Rule name
              </Text>
              <Input
                value={rule.name}
                onChange={(e) => onChange({ ...rule, name: e.target.value })}
                placeholder="Rule name"
              />
            </div>
            <div>
              <Text type="secondary" style={{ fontSize: 12 }}>
                Action
              </Text>
              <Select
                value={rule.action}
                onChange={(value) =>
                  onChange({ ...rule, action: value as any })
                }
                options={ACTION_OPTIONS}
                style={{ width: 120 }}
              />
            </div>
          </Flex>

          <div>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Denial message (optional)
            </Text>
            <Input
              value={rule.on_denial_message || ""}
              onChange={(e) =>
                onChange({ ...rule, on_denial_message: e.target.value })
              }
              placeholder="Message to show when this rule denies access"
            />
          </div>

          <div>
            <Flex justify="space-between" align="center">
              <Title level={5}>Match Conditions</Title>
              <Button
                onClick={handleAddMatch}
                size="small"
                icon={<Icons.Add />}
              >
                Add Match
              </Button>
            </Flex>
            {rule.matches.map((match, matchIndex) => (
              <RuleMatchEditor
                key={matchIndex}
                match={match}
                index={matchIndex}
                onChange={(m) => handleMatchChange(matchIndex, m)}
                onRemove={() => handleMatchRemove(matchIndex)}
              />
            ))}
            {rule.matches.length === 0 && (
              <Text type="secondary" italic>
                No match conditions. Click &quot;Add Match&quot; to add one.
              </Text>
            )}
          </div>

          <div>
            <Flex justify="space-between" align="center">
              <Title level={5}>Constraints</Title>
              <Button
                onClick={handleAddConstraint}
                size="small"
                icon={<Icons.Add />}
              >
                Add Constraint
              </Button>
            </Flex>
            {rule.constraints.map((constraint, constraintIndex) => (
              <RuleConstraintEditor
                key={constraintIndex}
                constraint={constraint}
                index={constraintIndex}
                onChange={(c) => handleConstraintChange(constraintIndex, c)}
                onRemove={() => handleConstraintRemove(constraintIndex)}
              />
            ))}
            {rule.constraints.length === 0 && (
              <Text type="secondary" italic>
                No constraints.{" "}
                {rule.action === "ALLOW"
                  ? "ALLOW rules with constraints require them to be satisfied."
                  : "DENY rules with constraints are lifted when constraints are satisfied (e.g., consent)."}
              </Text>
            )}
          </div>
        </Space>
      </Box>
    </Card>
  );
};

const PolicyV2Form = ({ policy }: { policy?: PolicyV2 }) => {
  const router = useRouter();
  const toast = useToast();

  const [createPolicy] = useCreatePolicyV2Mutation();
  const [updatePolicy] = useUpdatePolicyV2Mutation();

  // Only consider it "editing" if we have a policy with a valid id
  // Empty id means it's a new policy being prefilled (e.g., from AI chat)
  const isEditing = useMemo(() => !!policy && !!policy.id, [policy]);

  const initialValues: FormValues = useMemo(
    () =>
      policy
        ? {
            fides_key: policy.fides_key,
            name: policy.name,
            description: policy.description || "",
            enabled: policy.enabled,
            rules: policy.rules || [],
          }
        : {
            fides_key: "",
            name: "",
            description: "",
            enabled: true,
            rules: [],
          },
    [policy],
  );

  const handleSubmit = async (values: FormValues) => {
    const payload: PolicyV2Create = {
      fides_key: values.fides_key,
      name: values.name,
      description: values.description || null,
      enabled: values.enabled,
      rules: values.rules.map(({ id, order, ...rule }) => rule),
    };

    let result;
    if (isEditing) {
      result = await updatePolicy({
        fides_key: policy!.fides_key,
        name: values.name,
        description: values.description || null,
        enabled: values.enabled,
        rules: values.rules.map(({ id, order, ...rule }) => rule),
      });
    } else {
      result = await createPolicy(payload);
    }

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
    } else {
      toast(successToastParams(`Policy ${isEditing ? "updated" : "created"}`));
      if (!isEditing) {
        router.push(POLICIES_V2_ROUTE);
      }
    }
  };

  return (
    <Formik
      initialValues={initialValues}
      enableReinitialize
      onSubmit={handleSubmit}
      validationSchema={ValidationSchema}
    >
      {({ values, setFieldValue, dirty, isValid, isSubmitting }) => (
        <Form>
          <Stack spacing={10}>
            <Stack spacing={6}>
              <FormSection title="Policy Details">
                <CustomTextInput
                  label="Policy name"
                  name="name"
                  isRequired
                  variant="stacked"
                />
                <CustomTextInput
                  label="Fides key"
                  name="fides_key"
                  isRequired
                  variant="stacked"
                  disabled={isEditing}
                  tooltip="Unique identifier for this policy. Cannot be changed after creation."
                />
                <CustomTextArea
                  label="Description"
                  name="description"
                  variant="stacked"
                />
                <CustomSwitch
                  name="enabled"
                  label="Enable this policy"
                  variant="stacked"
                />
              </FormSection>

              <FormSection title="Rules">
                <VStack align="stretch" spacing={4}>
                  <Flex justify="flex-end">
                    <Button
                      type="primary"
                      icon={<Icons.Add />}
                      onClick={() =>
                        setFieldValue("rules", [
                          ...values.rules,
                          {
                            name: `Rule ${values.rules.length + 1}`,
                            action: "DENY",
                            matches: [],
                            constraints: [],
                          },
                        ])
                      }
                    >
                      Add Rule
                    </Button>
                  </Flex>
                  {values.rules.length === 0 && (
                    <Text type="secondary" italic>
                      No rules defined. Click &quot;Add Rule&quot; to create
                      one.
                    </Text>
                  )}
                  {values.rules.map((rule, index) => (
                    <RuleEditor
                      key={index}
                      rule={rule}
                      index={index}
                      onChange={(newRule) => {
                        const newRules = [...values.rules];
                        newRules[index] = newRule;
                        setFieldValue("rules", newRules);
                      }}
                      onRemove={() => {
                        setFieldValue(
                          "rules",
                          values.rules.filter((_, i) => i !== index),
                        );
                      }}
                    />
                  ))}
                </VStack>
              </FormSection>
            </Stack>
            <div className="flex gap-2">
              <Button onClick={() => router.back()}>Cancel</Button>
              <Button
                htmlType="submit"
                type="primary"
                disabled={isSubmitting || !dirty || !isValid}
                loading={isSubmitting}
                data-testid="save-btn"
              >
                Save
              </Button>
            </div>
          </Stack>
        </Form>
      )}
    </Formik>
  );
};

export default PolicyV2Form;
