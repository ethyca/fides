import {
  Button,
  ChakraBox as Box,
  ChakraCheckbox as Checkbox,
  ChakraDeleteIcon as DeleteIcon,
  ChakraFlex as Flex,
  ChakraSmallAddIcon as SmallAddIcon,
  ChakraText as Text,
} from "fidesui";
import { useFormikContext } from "formik";

import { ControlledSelect } from "~/features/common/form/ControlledSelect";
import { CustomTextInput } from "~/features/common/form/inputs";

import type { PropertyFormValues } from "../PropertyForm";

interface CustomFieldEntry {
  key: string;
  field_type?: string | null;
  label: string;
  required?: boolean | null;
  hidden?: boolean | null;
  ip_geolocation_hint?: boolean | null;
  default_value?: string | null;
}

const FIELD_TYPE_OPTIONS = [
  { value: "location", label: "Location" },
  { value: "text", label: "Text" },
  { value: "select", label: "Select" },
  { value: "multiselect", label: "Multi-select" },
];

const DEFAULT_CUSTOM_FIELD: CustomFieldEntry = {
  key: "",
  field_type: "text",
  label: "",
  required: true,
  hidden: false,
};

interface Props {
  actionIndex: number;
}

const CustomPrivacyFieldsArray = ({ actionIndex }: Props) => {
  const { values, setFieldValue } = useFormikContext<PropertyFormValues>();
  const basePath = `privacy_center_config.actions[${actionIndex}].custom_privacy_request_fields`;

  const fieldsMap =
    (values.privacy_center_config?.actions?.[actionIndex]
      ?.custom_privacy_request_fields as Record<
      string,
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      any
    >) ?? {};

  // We work with an ordered array of {key, ...fieldProps} entries for display,
  // then sync back to the dict format on every mutation.
  const entries: CustomFieldEntry[] = Object.entries(fieldsMap).map(
    ([key, val]) => ({ key, ...val }),
  );

  const syncToFormik = (updated: CustomFieldEntry[]) => {
    const dict: Record<string, unknown> = {};
    updated.forEach(({ key, ...rest }) => {
      if (key) {
        dict[key] = rest;
      }
    });
    setFieldValue(basePath, dict);
  };

  const handleAdd = () => {
    syncToFormik([
      ...entries,
      { ...DEFAULT_CUSTOM_FIELD, key: `field_${entries.length + 1}` },
    ]);
  };

  const handleRemove = (index: number) => {
    const updated = entries.filter((_, i) => i !== index);
    syncToFormik(updated);
  };

  const handleFieldChange = (
    index: number,
    field: keyof CustomFieldEntry,
    value: unknown,
  ) => {
    const updated = entries.map((entry, i) =>
      i === index ? { ...entry, [field]: value } : entry,
    );
    syncToFormik(updated);
  };

  return (
    <Flex flexDir="column" gap={3}>
      {entries.map((entry, index) => {
        const isLocation = entry.field_type === "location";
        return (
          <Box
            // eslint-disable-next-line react/no-array-index-key
            key={index}
            border="1px solid"
            borderColor="gray.100"
            borderRadius="md"
            p={3}
            data-testid={`custom-field-${actionIndex}-${index}`}
          >
            <Flex justifyContent="space-between" alignItems="center" mb={3}>
              <Text fontSize="xs" fontWeight="semibold" color="gray.600">
                Custom field {index + 1}
                {entry.label ? ` — ${entry.label}` : ""}
              </Text>
              <Button
                aria-label="Remove custom field"
                icon={<DeleteIcon />}
                onClick={() => handleRemove(index)}
                loading={false}
                data-testid={`remove-custom-field-${actionIndex}-${index}`}
              />
            </Flex>

            <Flex flexDir="column" gap={2}>
              <CustomTextInput
                label="Field key (internal name)"
                name={`__custom_key_${actionIndex}_${index}`}
                value={entry.key}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  handleFieldChange(index, "key", e.target.value)
                }
                variant="stacked"
              />
              <ControlledSelect
                label="Field type"
                name={`__custom_type_${actionIndex}_${index}`}
                value={entry.field_type ?? "text"}
                options={FIELD_TYPE_OPTIONS}
                layout="stacked"
                onChange={(val: string) =>
                  handleFieldChange(index, "field_type", val)
                }
              />
              <CustomTextInput
                label="Label"
                name={`__custom_label_${actionIndex}_${index}`}
                value={entry.label}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                  handleFieldChange(index, "label", e.target.value)
                }
                variant="stacked"
              />
              <Flex gap={4}>
                <Checkbox
                  isChecked={!!entry.required}
                  onChange={(e) =>
                    handleFieldChange(index, "required", e.target.checked)
                  }
                  data-testid={`custom-field-required-${actionIndex}-${index}`}
                >
                  <Text fontSize="sm">Required</Text>
                </Checkbox>
                {!isLocation && (
                  <Checkbox
                    isChecked={!!entry.hidden}
                    onChange={(e) =>
                      handleFieldChange(index, "hidden", e.target.checked)
                    }
                    data-testid={`custom-field-hidden-${actionIndex}-${index}`}
                  >
                    <Text fontSize="sm">Hidden</Text>
                  </Checkbox>
                )}
                {isLocation && (
                  <Checkbox
                    isChecked={!!entry.ip_geolocation_hint}
                    onChange={(e) =>
                      handleFieldChange(
                        index,
                        "ip_geolocation_hint",
                        e.target.checked,
                      )
                    }
                    data-testid={`custom-field-ip-hint-${actionIndex}-${index}`}
                  >
                    <Text fontSize="sm">IP geolocation hint</Text>
                  </Checkbox>
                )}
              </Flex>
              {entry.hidden && (
                <CustomTextInput
                  label="Default value (required when hidden)"
                  name={`__custom_default_${actionIndex}_${index}`}
                  value={entry.default_value ?? ""}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
                    handleFieldChange(index, "default_value", e.target.value)
                  }
                  variant="stacked"
                />
              )}
            </Flex>
          </Box>
        );
      })}
      <Box>
        <Button
          icon={<SmallAddIcon />}
          onClick={handleAdd}
          loading={false}
          data-testid={`add-custom-field-${actionIndex}`}
        >
          Add custom field
        </Button>
      </Box>
    </Flex>
  );
};

export default CustomPrivacyFieldsArray;
