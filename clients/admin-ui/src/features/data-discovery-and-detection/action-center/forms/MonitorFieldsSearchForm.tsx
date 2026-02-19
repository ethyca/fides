import { Button, Flex, Form, Icons, Select, Tooltip } from "fidesui";
import { capitalize } from "lodash";

import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import { TaxonomySelectOption } from "~/features/common/dropdown/TaxonomySelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import SearchInput from "~/features/common/SearchInput";
import useSearchForm from "~/features/data-discovery-and-detection/action-center/hooks/useSearchForm";
import { ConfidenceBucket } from "~/types/api/models/ConfidenceBucket";

import { RESOURCE_STATUS } from "../fields/MonitorFields.const";
import { MonitorFieldSearchForm } from "./MonitorFieldSearchForm.util";

const CONFIDENCE_BUCKETS: ConfidenceBucket[] = [
  ConfidenceBucket.HIGH,
  ConfidenceBucket.MEDIUM,
  ConfidenceBucket.LOW,
  ConfidenceBucket.MANUAL,
] as const;

const MonitorFieldsSearchForm = ({
  form,
  shortcutCallback,
  availableFilters,
  ...formProps
}: Omit<
  ReturnType<typeof useSearchForm<any, MonitorFieldSearchForm>>,
  "requestData"
> & {
  shortcutCallback: () => void;
  availableFilters: {
    data_category?: string[];
  };
}) => {
  const { getDataCategoryDisplayNameProps, getDataCategories } =
    useTaxonomies();

  const options: TaxonomySelectOption[] = getDataCategories().flatMap(
    (category) => {
      if (
        !category.active ||
        !availableFilters.data_category?.includes(category.fides_key)
      ) {
        return [];
      }
      const { name, primaryName } = getDataCategoryDisplayNameProps(
        category.fides_key,
      );
      return [
        {
          value: category.fides_key,
          name,
          primaryName,
          description: category.description || "",
          label: (
            <>
              <strong>{primaryName || name}</strong>
              {primaryName && `: ${name}`}
            </>
          ),
          title: category.fides_key,
        },
      ];
    },
  );

  return (
    <Form
      form={form}
      {...formProps}
      layout="inline"
      className="flex grow gap-2"
    >
      <Flex className="grow self-stretch">
        <Form.Item name="search" className="self-end">
          <SearchInput />
        </Form.Item>

        <Tooltip title="Display keyboard shortcuts">
          <Button
            aria-label="Display keyboard shortcuts"
            icon={<Icons.Keyboard />}
            onClick={shortcutCallback}
          />
        </Tooltip>
      </Flex>
      <Form.Item name="resource_status" className="!me-0 self-end">
        <Select
          options={RESOURCE_STATUS.map((resourceStatus) => ({
            value: resourceStatus,
            label: resourceStatus,
          }))}
          className="w-auto min-w-[200px]"
          placeholder="Status"
          allowClear
          aria-label="Filter by status"
          mode="multiple"
          maxTagCount="responsive"
        />
      </Form.Item>

      <Form.Item name="confidence_bucket" className="!me-0 self-end">
        <Select
          options={CONFIDENCE_BUCKETS.map((confidenceBucket) => ({
            value: confidenceBucket,
            label: capitalize(confidenceBucket),
          }))}
          className="w-auto min-w-[200px]"
          placeholder="Confidence"
          allowClear
          aria-label="Filter by confidence score"
          mode="multiple"
          maxTagCount="responsive"
        />
      </Form.Item>

      <Form.Item name="data_category" className="!me-0 self-end">
        <DataCategorySelect
          className="w-auto min-w-[220px]"
          variant="outlined"
          allowClear
          maxTagCount="responsive"
          placeholder="Data categories"
          mode="multiple"
          options={options}
          autoFocus={false}
        />
      </Form.Item>
    </Form>
  );
};

export default MonitorFieldsSearchForm;
