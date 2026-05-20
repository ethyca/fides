import { Button, Dropdown } from "fidesui";

import type { ComponentType } from "./catalog";
import { catalog } from "./catalog";
import type { JsonRenderSpec } from "./types";

type EditableComponentType = Exclude<ComponentType, "Form">;

const FIELD_TYPE_LABELS: Record<EditableComponentType, string> = {
  Text: "Text input",
  Select: "Single-select dropdown",
  MultiSelect: "Multi-select dropdown",
  Radio: "Radio group",
  Location: "Location picker",
  Email: "Email",
  Name: "Name",
  Phone: "Phone",
};

// Fixed element IDs for identity types — used to detect duplicates in the spec.
const IDENTITY_ELEMENT_IDS: Partial<Record<EditableComponentType, string>> = {
  Email: "f_email",
  Name: "f_name",
  Phone: "f_phone",
};

// Identity types in the canonical PC render order (Name → Email → Phone).
const IDENTITY_TYPES_ORDERED: EditableComponentType[] = [
  "Name",
  "Email",
  "Phone",
];
const IDENTITY_TYPE_SET = new Set<string>(IDENTITY_TYPES_ORDERED);

// Custom (non-identity) types in alphabetical order.
const CUSTOM_TYPES_ORDERED: EditableComponentType[] = (
  Object.keys(catalog.components).filter(
    (k) => k !== "Form" && !IDENTITY_TYPE_SET.has(k),
  ) as EditableComponentType[]
).sort();

interface AddFieldButtonProps {
  onAddField: (type: EditableComponentType) => void;
  spec: JsonRenderSpec | null;
}

export const AddFieldButton = ({ onAddField, spec }: AddFieldButtonProps) => {
  const availableIdentity = IDENTITY_TYPES_ORDERED.filter((type) => {
    const fixedId = IDENTITY_ELEMENT_IDS[type];
    return !fixedId || !spec?.elements[fixedId];
  });

  const identityItems = availableIdentity.map((type) => ({
    key: type,
    label: <strong>{FIELD_TYPE_LABELS[type]}</strong>,
  }));

  const customItems = CUSTOM_TYPES_ORDERED.map((type) => ({
    key: type,
    label: FIELD_TYPE_LABELS[type],
  }));

  const items = [
    ...identityItems,
    ...(identityItems.length > 0 && customItems.length > 0
      ? [{ type: "divider" as const }]
      : []),
    ...customItems,
  ];

  return (
    <Dropdown
      menu={{
        items,
        onClick: ({ key }) => onAddField(key as EditableComponentType),
      }}
    >
      <Button data-testid="add-field-button" type="dashed" block>
        + Add field
      </Button>
    </Dropdown>
  );
};
