import { useEffect, useMemo, useRef, useState } from "react";
import * as Yup from "yup";

import { useApplicableFields } from "~/hooks/useApplicableFields";
import { CustomConfigField } from "~/types/config";
import { FormValues } from "~/types/forms";

/**
 * Sets up the Formik `validate` function with conditional-field awareness.
 * Call this before `useFormik` — it returns a `validate` function that reads
 * from refs so it always sees the latest applicable field set.
 */
export const useConditionalValidate = ({
  customPrivacyRequestFields,
  identityValidationSchema,
  getValidationSchema,
}: {
  customPrivacyRequestFields: Record<string, CustomConfigField>;
  identityValidationSchema: Yup.AnyObjectSchema;
  getValidationSchema: (applicable: Set<string>) => Yup.AnyObjectSchema;
}) => {
  const [validationError, setValidationError] = useState(false);

  const applicableFieldsRef = useRef<Set<string>>(
    new Set(Object.keys(customPrivacyRequestFields)),
  );

  // Invalidate the schema cache when the field config changes, so a
  // re-conditionalized field (same applicable key set, different rules)
  // doesn't serve a stale schema.
  const configSignature = useMemo(
    () => JSON.stringify(Object.keys(customPrivacyRequestFields).sort()),
    [customPrivacyRequestFields],
  );

  // Cache the last applicable-aware schema to avoid rebuilding on every keystroke
  const schemaCache = useRef<{
    applicableKey: string;
    configSignature: string;
    schema: Yup.AnyObjectSchema;
  } | null>(null);

  const validate = (values: FormValues) => {
    setValidationError(false);
    const currentApplicable = applicableFieldsRef.current;
    const applicableKey = Array.from(currentApplicable).sort().join(",");
    let combinedSchema: Yup.AnyObjectSchema;

    if (
      schemaCache.current?.applicableKey === applicableKey &&
      schemaCache.current?.configSignature === configSignature
    ) {
      combinedSchema = schemaCache.current.schema;
    } else {
      const customFieldSchema = getValidationSchema(currentApplicable);
      combinedSchema = identityValidationSchema.concat(
        customFieldSchema,
      ) as Yup.AnyObjectSchema;
      schemaCache.current = {
        applicableKey,
        configSignature,
        schema: combinedSchema,
      };
    }

    try {
      combinedSchema.validateSync(values, { abortEarly: false });
      return {};
    } catch (err) {
      if (err instanceof Yup.ValidationError) {
        const errors: Record<string, string> = {};
        err.inner.forEach((e) => {
          if (e.path && !errors[e.path]) {
            errors[e.path] = e.message;
          }
        });
        return errors;
      }
      setValidationError(true);
      return { _form: "An unexpected error occurred." };
    }
  };

  return { validate, applicableFieldsRef, validationError };
};

/**
 * Resolves which custom fields are currently applicable and clears values
 * for fields that become non-applicable. Call this after `useFormik`.
 */
export const useApplicabilitySync = ({
  customPrivacyRequestFields,
  applicableFieldsRef,
  initialValues,
  formValues,
  setFieldValue,
}: {
  customPrivacyRequestFields: Record<string, CustomConfigField>;
  applicableFieldsRef: React.MutableRefObject<Set<string>>;
  initialValues: FormValues;
  formValues: FormValues;
  setFieldValue: (field: string, value: unknown) => void;
}): { applicableFields: Set<string>; conditionError: boolean } => {
  const { applicableFields, conditionError } = useApplicableFields(
    customPrivacyRequestFields,
    formValues,
  );
  // Update the ref synchronously so the validate function (which reads from
  // this ref) always sees the latest applicable set during the same render.
  // eslint-disable-next-line no-param-reassign
  applicableFieldsRef.current = applicableFields;

  const prevApplicable = useRef<Set<string>>(applicableFields);
  useEffect(() => {
    const prev = prevApplicable.current;
    prevApplicable.current = applicableFields;

    prev.forEach((key) => {
      if (!applicableFields.has(key) && key in customPrivacyRequestFields) {
        const fieldInitial = initialValues[key];
        const current = formValues[key];
        const unchanged =
          current === fieldInitial ||
          (Array.isArray(current) &&
            Array.isArray(fieldInitial) &&
            JSON.stringify(current) === JSON.stringify(fieldInitial));
        if (!unchanged) {
          setFieldValue(key, fieldInitial ?? "");
        }
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [applicableFields]);

  return { applicableFields, conditionError };
};
