import {
  Descriptions,
  InputNumber,
  Select,
  Switch,
  Text,
  Title,
} from "fidesui";
import { useMemo } from "react";

import { useGetAllDataCategoriesQuery } from "~/features/taxonomy/data-category.slice";
import { useGetAllDataSubjectsQuery } from "~/features/data-subjects/data-subject.slice";
import { useGetAllDataUsesQuery } from "~/features/data-use/data-use.slice";

import {
  FEATURE_OPTIONS,
  LEGAL_BASIS_OPTIONS,
  SPECIAL_CATEGORY_LEGAL_BASIS_OPTIONS,
} from "./constants";
import type { DataPurpose } from "./types";

interface PurposeConfigSectionProps {
  purpose: DataPurpose;
  onFieldChange: (field: string, value: unknown) => void;
}

const PurposeConfigSection = ({
  purpose,
  onFieldChange,
}: PurposeConfigSectionProps) => {
  const { data: dataUses } = useGetAllDataUsesQuery();
  const { data: dataCategories } = useGetAllDataCategoriesQuery();
  const { data: dataSubjects } = useGetAllDataSubjectsQuery();

  const dataUseOptions = useMemo(
    () =>
      (dataUses ?? []).map((du) => ({
        value: du.fides_key,
        label: du.fides_key,
      })),
    [dataUses],
  );

  const dataCategoryOptions = useMemo(
    () =>
      (dataCategories ?? []).map((dc) => ({
        value: dc.fides_key,
        label: dc.fides_key,
      })),
    [dataCategories],
  );

  const dataSubjectOptions = useMemo(
    () =>
      (dataSubjects ?? []).map((ds) => ({
        value: ds.fides_key,
        label: ds.fides_key,
      })),
    [dataSubjects],
  );

  return (
    <div>
      <Title
        level={5}
        className="mb-2 text-[10px] uppercase tracking-[0.1em]"
        type="secondary"
      >
        Configuration
      </Title>
      <Descriptions bordered size="small" column={2}>
        <Descriptions.Item label="Key">
          <Text copyable>{purpose.key}</Text>
        </Descriptions.Item>
        <Descriptions.Item label="Data use">
          <Select
            variant="borderless"
            showSearch
            className="w-full"
            options={dataUseOptions}
            value={purpose.data_use}
            onChange={(val) => onFieldChange("data_use", val)}
            placeholder="Select data use"
          />
        </Descriptions.Item>
        <Descriptions.Item label="Data categories" span={2}>
          <Select
            mode="multiple"
            variant="borderless"
            className="w-full"
            options={dataCategoryOptions}
            value={purpose.data_categories}
            onChange={(val) => onFieldChange("data_categories", val)}
            placeholder="Select data categories"
            showSearch
          />
        </Descriptions.Item>
        <Descriptions.Item label="Data subjects" span={2}>
          <Select
            mode="multiple"
            variant="borderless"
            className="w-full"
            options={dataSubjectOptions}
            value={purpose.data_subjects}
            onChange={(val) => onFieldChange("data_subjects", val)}
            placeholder="Select data subjects"
            showSearch
          />
        </Descriptions.Item>
        <Descriptions.Item label="Legal basis">
          <Select
            variant="borderless"
            className="w-full"
            options={LEGAL_BASIS_OPTIONS}
            value={purpose.legal_basis}
            onChange={(val) => onFieldChange("legal_basis", val)}
            placeholder="Select legal basis"
          />
        </Descriptions.Item>
        <Descriptions.Item label="Flexible basis">
          <Switch
            size="small"
            checked={purpose.legal_basis_is_flexible}
            onChange={(val) => onFieldChange("legal_basis_is_flexible", val)}
          />
        </Descriptions.Item>
        <Descriptions.Item label="Retention (days)">
          <InputNumber
            variant="borderless"
            className="w-full"
            min={0}
            value={purpose.retention_period_days}
            onChange={(val) => onFieldChange("retention_period_days", val)}
            placeholder="Enter days"
          />
        </Descriptions.Item>
        <Descriptions.Item label="Special category basis">
          <Select
            variant="borderless"
            className="w-full"
            options={SPECIAL_CATEGORY_LEGAL_BASIS_OPTIONS}
            value={purpose.special_category_legal_basis}
            onChange={(val) => onFieldChange("special_category_legal_basis", val)}
            placeholder="Select basis"
            allowClear
          />
        </Descriptions.Item>
        <Descriptions.Item label="Features" span={2}>
          <Select
            mode="multiple"
            variant="borderless"
            className="w-full"
            options={FEATURE_OPTIONS}
            value={purpose.features}
            onChange={(val) => onFieldChange("features", val)}
            placeholder="Select features"
          />
        </Descriptions.Item>
      </Descriptions>
    </div>
  );
};

export default PurposeConfigSection;
