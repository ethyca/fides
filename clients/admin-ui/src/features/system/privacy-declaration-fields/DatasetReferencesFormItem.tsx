import { Form, Select } from "fidesui";

import DatasetSelectOption from "~/features/dataset/DatasetSelectOption";
import { Dataset } from "~/types/api";

interface DatasetReferencesFormItemProps {
  allDatasets: Dataset[];
  disabled?: boolean;
}

export const DatasetReferencesFormItem = ({
  allDatasets,
  disabled,
}: DatasetReferencesFormItemProps) => (
  <Form.Item
    name="dataset_references"
    label="Dataset references"
    tooltip="Referenced Dataset fides keys used by the system."
  >
    <Select
      aria-label="Dataset references"
      mode="multiple"
      data-testid="input-dataset_references"
      disabled={disabled}
      options={allDatasets.map((ds) => ({
        value: ds.fides_key,
        label: ds.name ?? ds.fides_key,
      }))}
      optionRender={DatasetSelectOption}
      showSearch
      optionFilterProp="label"
    />
  </Form.Item>
);
