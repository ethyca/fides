import classNames from "classnames";
import { Form, FormRule, Input, InputNumber, Switch } from "fidesui";
import { useEffect, useRef } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectDictEntry } from "~/features/plus/plus.slice";
import { selectSuggestions } from "~/features/system/dictionary-form/dict-suggestion.slice";
import { Vendor } from "~/types/dictionary-api";

import styles from "./DictSuggestionInputs.module.scss";

interface BaseProps {
  name: string;
  label: string;
  tooltip?: string;
  disabled?: boolean;
  id?: string;
  dictField?: (vendor: Vendor) => string | boolean | number | undefined | null;
}

interface TextFieldProps extends BaseProps {
  isRequired?: boolean;
}

/**
 * Watches the global "showing"/"hiding" Compass suggestion lifecycle and rewrites
 * the corresponding field on the antd form instance. On "showing" we snapshot the
 * current value so we can restore it on "hiding".
 */
const useDictSuggestion = (
  fieldName: string,
  dictField?: BaseProps["dictField"],
) => {
  const form = Form.useFormInstance();
  const fieldValue = Form.useWatch(fieldName, form);
  const vendorId = Form.useWatch<string | undefined>("vendor_id", form);
  const suggestionsState = useAppSelector(selectSuggestions);
  const dictEntry = useAppSelector(selectDictEntry(vendorId || ""));
  const preSuggestionRef = useRef<unknown>(undefined);
  const hasCapturedRef = useRef(false);

  useEffect(() => {
    if (suggestionsState === "showing") {
      preSuggestionRef.current = form.getFieldValue(fieldName);
      hasCapturedRef.current = true;
      if (dictEntry) {
        const suggested = dictField
          ? dictField(dictEntry)
          : (dictEntry[fieldName as keyof Vendor] as
              | string
              | boolean
              | number
              | undefined);
        if (
          suggested !== undefined &&
          suggested !== form.getFieldValue(fieldName)
        ) {
          form.setFieldValue(fieldName, suggested);
        }
      }
    } else if (suggestionsState === "hiding" && hasCapturedRef.current) {
      // Only restore when we actually captured a pre-suggestion value;
      // otherwise we'd overwrite a legitimate initial value with `undefined`
      // (e.g. when "hiding" fires from clearing the vendor without ever
      // having shown suggestions).
      form.setFieldValue(fieldName, preSuggestionRef.current);
      hasCapturedRef.current = false;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [suggestionsState, dictEntry]);

  return {
    isShowingSuggestions: suggestionsState === "showing",
    value: fieldValue,
  };
};

export const DictSuggestionTextInput = ({
  name,
  label,
  tooltip,
  disabled,
  isRequired,
  id,
  dictField,
  placeholder,
  rules,
}: TextFieldProps & { placeholder?: string; rules?: FormRule[] }) => {
  const { isShowingSuggestions } = useDictSuggestion(name, dictField);
  const composedRules: FormRule[] = [
    ...(isRequired
      ? [{ required: true, message: `${label} is required` }]
      : []),
    ...(rules ?? []),
  ];
  return (
    <Form.Item
      name={name}
      label={label}
      tooltip={tooltip}
      required={isRequired}
      rules={composedRules.length > 0 ? composedRules : undefined}
    >
      <Input
        id={id || name}
        disabled={disabled}
        placeholder={placeholder}
        data-testid={`input-${name}`}
        className={classNames({ [styles.suggested]: isShowingSuggestions })}
      />
    </Form.Item>
  );
};

export const DictSuggestionTextArea = ({
  name,
  label,
  tooltip,
  disabled,
  isRequired,
  id,
  dictField,
}: TextFieldProps) => {
  const { isShowingSuggestions } = useDictSuggestion(name, dictField);
  return (
    <Form.Item
      name={name}
      label={label}
      tooltip={tooltip}
      required={isRequired}
      rules={
        isRequired
          ? [{ required: true, message: `${label} is required` }]
          : undefined
      }
    >
      <Input.TextArea
        id={id || name}
        disabled={disabled}
        data-testid={`input-${name}`}
        className={classNames({ [styles.suggested]: isShowingSuggestions })}
      />
    </Form.Item>
  );
};

export const DictSuggestionSwitch = ({
  name,
  label,
  tooltip,
  disabled,
  id,
  dictField,
}: BaseProps) => {
  useDictSuggestion(name, dictField);
  return (
    <Form.Item
      name={name}
      label={label}
      tooltip={tooltip}
      layout="horizontal"
      colon={false}
      valuePropName="checked"
      className="mb-0"
    >
      <Switch
        id={id || name}
        disabled={disabled}
        size="small"
        data-testid={`input-${name}`}
      />
    </Form.Item>
  );
};

export const DictSuggestionNumberInput = ({
  name,
  label,
  tooltip,
  disabled,
  id,
  dictField,
}: BaseProps) => {
  const { isShowingSuggestions } = useDictSuggestion(name, dictField);
  return (
    <Form.Item
      name={name}
      label={label}
      tooltip={tooltip}
      layout="horizontal"
      colon={false}
      className="mb-0"
    >
      <InputNumber
        id={id || name}
        disabled={disabled}
        data-testid={`input-${name}`}
        className={classNames("w-full", {
          [styles.suggested]: isShowingSuggestions,
        })}
      />
    </Form.Item>
  );
};
