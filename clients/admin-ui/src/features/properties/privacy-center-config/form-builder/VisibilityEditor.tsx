import { Button, Card, Icons, Input, Radio, Select, Space } from "fidesui";
import dynamic from "next/dynamic";

import type { JsonRenderSpec } from "./types";

// LocationSelect transitively imports iso-3166 (CJS), which Turbopack rejects
// on the SSR path. Mirror the dynamic-import pattern used by LocationField.
const LocationSelect = dynamic(
  () => import("fidesui").then((m) => m.LocationSelect),
  { ssr: false },
);

type Operator = "eq" | "ne" | "set" | "empty" | "contains";

const OPERATOR_LABELS: Record<Operator, string> = {
  eq: "equals",
  ne: "does not equal",
  set: "is set",
  empty: "is empty",
  contains: "contains",
};

const OPERATORS_NEEDING_VALUE: Operator[] = ["eq", "ne", "contains"];

/** A single condition row in the editor's UI state. */
export interface ConditionRow {
  fieldName: string;
  operator: Operator;
  /** String form for the input — coerced to the right shape on serialization. */
  value: string;
}

interface SerializedCondition {
  $state: string;
  eq?: unknown;
  ne?: unknown;
  set?: boolean;
  empty?: boolean;
  contains?: unknown;
}

/** Convert UI rows → JsonRenderElement.visible value. */
export const rowsToVisible = (
  rows: ConditionRow[],
): SerializedCondition[] | undefined => {
  const populated = rows.filter((r) => r.fieldName);
  if (populated.length === 0) {
    return undefined;
  }
  return populated.map((row) => {
    const cond: SerializedCondition = { $state: `/form/${row.fieldName}` };
    switch (row.operator) {
      case "set":
        cond.set = true;
        break;
      case "empty":
        cond.empty = true;
        break;
      case "eq":
      case "ne":
      case "contains":
        cond[row.operator] = row.value;
        break;
      default:
        break;
    }
    return cond;
  });
};

/** Convert a saved JsonRenderElement.visible back into UI rows. */
export const visibleToRows = (visible: unknown): ConditionRow[] => {
  if (!Array.isArray(visible)) {
    return [];
  }
  return visible
    .map((entry): ConditionRow | null => {
      if (!entry || typeof entry !== "object") {
        return null;
      }
      const obj = entry as Record<string, unknown>;
      const path = typeof obj.$state === "string" ? obj.$state : "";
      const fieldName = path.startsWith("/form/")
        ? path.slice("/form/".length)
        : path;
      let operator: Operator = "eq";
      let value: unknown;
      if (obj.set === true) {
        operator = "set";
      } else if (obj.empty === true) {
        operator = "empty";
      } else if ("ne" in obj) {
        operator = "ne";
        value = obj.ne;
      } else if ("contains" in obj) {
        operator = "contains";
        value = obj.contains;
      } else if ("eq" in obj) {
        operator = "eq";
        value = obj.eq;
      }
      return {
        fieldName,
        operator,
        value: value === undefined || value === null ? "" : String(value),
      };
    })
    .filter((r): r is ConditionRow => r !== null);
};

interface VisibilityEditorProps {
  spec: JsonRenderSpec | null;
  /** The element id whose visibility is being edited (excluded from "field" picker). */
  selectedElementId: string;
  rows: ConditionRow[];
  onChange: (next: ConditionRow[]) => void;
}

const sourceFieldOptions = (
  spec: JsonRenderSpec | null,
  excludedId: string,
): Array<{ label: string; value: string; type: string }> => {
  if (!spec) {
    return [];
  }
  return Object.entries(spec.elements)
    .filter(
      ([id, el]) =>
        id !== excludedId &&
        id !== spec.root &&
        el.type !== "Form" &&
        typeof (el.props as { name?: string }).name === "string",
    )
    .map(([, el]) => {
      const props = el.props as { name?: string; label?: string };
      return {
        label: props.label ? `${props.label} (${props.name})` : props.name!,
        value: props.name!,
        type: el.type,
      };
    });
};

type SourceValueMode =
  | { kind: "options"; values: string[] }
  | { kind: "location" }
  | { kind: "free_text" };

const sourceValueMode = (
  spec: JsonRenderSpec | null,
  fieldName: string | undefined,
): SourceValueMode => {
  if (!spec || !fieldName) {
    return { kind: "free_text" };
  }
  const match = Object.values(spec.elements).find(
    (el) => (el.props as { name?: string }).name === fieldName,
  );
  if (!match) {
    return { kind: "free_text" };
  }
  if (
    match.type !== "Select" &&
    match.type !== "MultiSelect" &&
    match.type !== "Radio" &&
    match.type !== "Location"
  ) {
    return { kind: "free_text" };
  }
  const opts = (match.props as { options?: unknown }).options;
  if (Array.isArray(opts) && opts.length > 0) {
    return { kind: "options", values: opts as string[] };
  }
  // Location with no custom options uses the full ISO list — render the
  // LocationSelect picker so authors pick a real ISO code instead of typing.
  if (match.type === "Location") {
    return { kind: "location" };
  }
  return { kind: "free_text" };
};

export const VisibilityEditor = ({
  spec,
  selectedElementId,
  rows,
  onChange,
}: VisibilityEditorProps) => {
  const fieldOptions = sourceFieldOptions(spec, selectedElementId);

  const updateRow = (idx: number, patch: Partial<ConditionRow>) => {
    onChange(rows.map((r, i) => (i === idx ? { ...r, ...patch } : r)));
  };

  const removeRow = (idx: number) => {
    onChange(rows.filter((_, i) => i !== idx));
  };

  const addRow = () => {
    onChange([...rows, { fieldName: "", operator: "eq", value: "" }]);
  };

  const isAlwaysShow = rows.length === 0;

  return (
    <Space orientation="vertical" className="w-full">
      <Radio.Group
        value={isAlwaysShow ? "always" : "conditional"}
        onChange={(e) => {
          if (e.target.value === "always") {
            onChange([]);
          } else {
            addRow();
          }
        }}
        options={[
          { label: "Always show", value: "always" },
          { label: "Show when…", value: "conditional" },
        ]}
        data-testid="visibility-mode"
      />
      {!isAlwaysShow && (
        <Space orientation="vertical" className="w-full">
          {rows.map((row, idx) => {
            const valueMode = sourceValueMode(spec, row.fieldName);
            const needsValue = OPERATORS_NEEDING_VALUE.includes(row.operator);
            // Stable-ish key per row position. Conditions are append-only;
            // editing a row doesn't shuffle others.
            const rowKey = `${idx}-${row.fieldName || "_"}-${row.operator}`;
            return (
              <Card key={rowKey} size="small">
                <Space orientation="vertical" className="w-full" size="small">
                  <Select
                    aria-label="Source field"
                    placeholder="Field"
                    className="w-full"
                    value={row.fieldName || undefined}
                    onChange={(v) => updateRow(idx, { fieldName: v })}
                    options={fieldOptions}
                    data-testid={`visibility-field-${idx}`}
                  />
                  <Select
                    aria-label="Operator"
                    className="w-full"
                    value={row.operator}
                    onChange={(v) => updateRow(idx, { operator: v })}
                    options={(Object.keys(OPERATOR_LABELS) as Operator[]).map(
                      (op) => ({ label: OPERATOR_LABELS[op], value: op }),
                    )}
                    data-testid={`visibility-operator-${idx}`}
                  />
                  {needsValue && valueMode.kind === "options" && (
                    <Select
                      aria-label="Value"
                      placeholder="Value"
                      className="w-full"
                      value={row.value || undefined}
                      onChange={(v) => updateRow(idx, { value: v })}
                      options={valueMode.values.map((o) => ({
                        label: o,
                        value: o,
                      }))}
                      data-testid={`visibility-value-${idx}`}
                    />
                  )}
                  {needsValue && valueMode.kind === "location" && (
                    <LocationSelect
                      aria-label="Value"
                      placeholder="Value"
                      className="w-full"
                      value={row.value || undefined}
                      onChange={(v: string) => updateRow(idx, { value: v })}
                      data-testid={`visibility-value-${idx}`}
                    />
                  )}
                  {needsValue && valueMode.kind === "free_text" && (
                    <Input
                      aria-label="Value"
                      placeholder="Value"
                      className="w-full"
                      value={row.value}
                      onChange={(e) =>
                        updateRow(idx, { value: e.target.value })
                      }
                      data-testid={`visibility-value-${idx}`}
                    />
                  )}
                </Space>
                <Button
                  size="small"
                  type="text"
                  icon={<Icons.TrashCan />}
                  onClick={() => removeRow(idx)}
                  aria-label="Remove condition"
                  data-testid={`visibility-remove-${idx}`}
                  className="self-end"
                >
                  Remove condition
                </Button>
              </Card>
            );
          })}
          <Button
            size="small"
            block
            onClick={addRow}
            data-testid="visibility-add"
          >
            + Add another condition (AND)
          </Button>
        </Space>
      )}
    </Space>
  );
};
