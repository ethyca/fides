import {
  AntAlert as Alert,
  AntButton as Button,
  AntFlex as Flex,
  AntForm as Form,
  AntInput as Input,
  AntModal as Modal,
  AntSelect as Select,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import { useMemo, useState } from "react";

import { useGetPrivacyCenterConfigQuery } from "~/features/privacy-requests/privacy-requests.slice";

interface CustomFieldFilter {
  id: string;
  field: string;
  value: string;
}

interface AdvancedSearchModalProps {
  open: boolean;
  onClose: () => void;
}

export const AdvancedSearchModal = ({
  open,
  onClose,
}: AdvancedSearchModalProps) => {
  const { data: config } = useGetPrivacyCenterConfigQuery();
  const [filters, setFilters] = useState<CustomFieldFilter[]>([
    { id: crypto.randomUUID(), field: "", value: "" },
  ]);

  // Extract unique custom field names from all actions
  const customFieldOptions = useMemo(() => {
    if (!config?.actions) {
      return [];
    }

    const fieldsMap = new Map<string, string>();
    config.actions.forEach((action) => {
      if (action.custom_privacy_request_fields) {
        Object.entries(action.custom_privacy_request_fields).forEach(
          ([fieldName, fieldInfo]) => {
            // Filter out location type fields
            if (
              "field_type" in fieldInfo &&
              fieldInfo.field_type === "location"
            ) {
              return;
            }
            // Use label if available, fallback to field name
            const label = fieldInfo.label || fieldName;
            fieldsMap.set(fieldName, label);
          },
        );
      }
    });

    return Array.from(fieldsMap.entries()).map(([fieldName, label]) => ({
      label,
      value: fieldName,
    }));
  }, [config]);

  const hasCustomFields = customFieldOptions.length > 0;

  const handleAddField = () => {
    setFilters([...filters, { id: crypto.randomUUID(), field: "", value: "" }]);
  };

  const handleRemoveField = (id: string) => {
    const newFilters = filters.filter((filter) => filter.id !== id);
    setFilters(newFilters);
  };

  const handleFieldChange = (
    id: string,
    key: keyof Omit<CustomFieldFilter, "id">,
    value: string,
  ) => {
    const newFilters = filters.map((filter) =>
      filter.id === id ? { ...filter, [key]: value } : filter,
    );
    setFilters(newFilters);
  };

  const handleClear = () => {
    setFilters([{ id: crypto.randomUUID(), field: "", value: "" }]);
  };

  const handleSearch = () => {
    // eslint-disable-next-line no-console
    console.log("Custom field filters:", filters);
    onClose();
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="Advanced search"
      width={600}
      footer={
        <Flex justify="space-between" align="center">
          <Button data-testid="clear-btn" onClick={handleClear}>
            Clear
          </Button>
          <Flex gap="small">
            <Button data-testid="cancel-btn" onClick={onClose}>
              Cancel
            </Button>
            <Button
              data-testid="search-btn"
              type="primary"
              onClick={handleSearch}
            >
              Search
            </Button>
          </Flex>
        </Flex>
      }
    >
      <Flex vertical gap="middle">
        {!hasCustomFields && (
          <Alert
            type="info"
            message={
              <Typography.Text>
                Advanced search requires posting your privacy center config to
                the API to be able to list your custom fields. For instructions,
                see the documentation{" "}
                <Typography.Link
                  href="https://www.ethyca.com/docs/dev-docs/privacy-center/configuration#admin-ui-privacy-requests-configuration"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  here
                </Typography.Link>
                .
              </Typography.Text>
            }
          />
        )}

        <Form layout="vertical">
          <Form.Item label="Custom fields">
            <Flex vertical gap="small">
              {filters.map((filter, index) => (
                <Flex key={filter.id} gap="small" align="center">
                  <Select
                    data-testid={`custom-field-select-${index}`}
                    style={{ flex: 1 }}
                    placeholder="Select field"
                    options={customFieldOptions}
                    value={filter.field || undefined}
                    onChange={(value) =>
                      handleFieldChange(filter.id, "field", value as string)
                    }
                    disabled={!hasCustomFields}
                    aria-label="Select a custom field"
                  />
                  <Flex flex={1} gap="small" align="center">
                    <Input
                      data-testid={`custom-field-input-${index}`}
                      placeholder="Search value"
                      value={filter.value}
                      onChange={(e) =>
                        handleFieldChange(filter.id, "value", e.target.value)
                      }
                      disabled={!hasCustomFields}
                    />
                    {index > 0 && (
                      <Button
                        data-testid="remove-field-btn"
                        icon={<Icons.TrashCan />}
                        onClick={() => handleRemoveField(filter.id)}
                        aria-label="Remove field"
                      />
                    )}
                  </Flex>
                </Flex>
              ))}
              <div>
                <Button
                  data-testid="add-field-btn"
                  icon={<Icons.Add />}
                  onClick={handleAddField}
                  disabled={!hasCustomFields}
                  size="small"
                >
                  Add field
                </Button>
              </div>
            </Flex>
          </Form.Item>
        </Form>
      </Flex>
    </Modal>
  );
};
