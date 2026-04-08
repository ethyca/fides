import { Button, Form, Icons, Select, Tooltip } from "fidesui";
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

const RESOURCE_STATUS_OPTIONS: Omit<
  (typeof RESOURCE_STATUS)[number],
  "Ignored" | "Approved" | "Approving" | "Removing"
>[] = [
  "Unlabeled",
  "Classifying",
  "Classified",
  "Reviewed",
  "Removed",
  "Error",
];

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
    <Form form={form} {...formProps} layout="inline" className="contents">
      <Form.Item name="search" className="col-span-2 !me-0 xl:col-span-1">
        <SearchInput className="!min-w-[200px]" />
      </Form.Item>

      <Tooltip title="Display keyboard shortcuts">
        <Button
          aria-label="Display keyboard shortcuts"
          icon={<Icons.Keyboard />}
          onClick={shortcutCallback}
          className="col-span-3 xl:col-span-1"
        />
      </Tooltip>
      <Form.Item name="resource_status" className="!me-0">
        <Select
          options={RESOURCE_STATUS_OPTIONS.map((resourceStatus) => ({
            value: resourceStatus,
            label: resourceStatus,
          }))}
          placeholder="Status"
          allowClear
          aria-label="Filter by status"
          mode="multiple"
          maxTagCount="responsive"
        />
      </Form.Item>

      <Form.Item name="confidence_bucket" className="!me-0">
        <Select
          options={CONFIDENCE_BUCKETS.map((confidenceBucket) => ({
            value: confidenceBucket,
            label: capitalize(confidenceBucket),
          }))}
          placeholder="Confidence"
          allowClear
          aria-label="Filter by confidence score"
          mode="multiple"
          maxTagCount="responsive"
        />
      </Form.Item>

      <Form.Item name="data_category" className="!me-0 overflow-hidden">
        <DataCategorySelect
          rootClassName="overflow-hidden"
          variant="outlined"
          allowClear
          maxTagCount="responsive"
          placeholder="Data categories"
          mode="multiple"
          options={options}
          autoFocus={false}
          popupMatchSelectWidth={false}
        />
      </Form.Item>
    </Form>
  );
};

export default MonitorFieldsSearchForm;
