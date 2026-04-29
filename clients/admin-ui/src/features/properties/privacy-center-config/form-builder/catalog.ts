import { defineCatalog } from "@json-render/core";
import { schema } from "@json-render/react/schema";
import { z } from "zod";

const SNAKE_CASE = /^[a-z][a-z0-9_]{0,63}$/;
const fieldName = z.string().regex(SNAKE_CASE, "snake_case, ≤ 64 chars");

const baseField = {
  name: fieldName,
  label: z.string().min(1),
  required: z.boolean(),
};

const components = {
  Form: {
    props: z.object({}).strict(),
    description:
      "Container for all fields in this form. Has no own props; children list field elements.",
  },
  Text: {
    props: z
      .object({
        ...baseField,
        default_value: z.string().nullable().optional(),
        hidden: z.boolean().optional(),
        query_param_key: z.string().nullable().optional(),
      })
      .strict(),
    description: "Single-line text input.",
  },
  Select: {
    props: z
      .object({
        ...baseField,
        options: z.array(z.string()).min(1),
        default_value: z.string().nullable().optional(),
      })
      .strict(),
    description: "Single-choice dropdown.",
  },
  MultiSelect: {
    props: z
      .object({
        ...baseField,
        options: z.array(z.string()).min(1),
        default_value: z.array(z.string()).nullable().optional(),
      })
      .strict(),
    description: "Multi-choice dropdown.",
  },
  Location: {
    props: z
      .object({
        ...baseField,
        options: z.array(z.string()).optional(),
        ip_geolocation_hint: z.boolean().optional(),
      })
      .strict(),
    description: "Location picker (country / region).",
  },
} as const;

const actions = {} as const;

// json-render's defineCatalog stores its input under `.data`. We expose the
// component/action maps at the top level for ergonomic access (matching the
// shape the rest of the form-builder consumes), while retaining the underlying
// json-render Catalog instance under `.jsonRender` for prompts, validation,
// and JSON Schema export.
const jsonRenderCatalog = defineCatalog(schema, { components, actions });

export const catalog = {
  jsonRender: jsonRenderCatalog,
  components,
  actions,
};

export type ComponentType = keyof typeof components;
