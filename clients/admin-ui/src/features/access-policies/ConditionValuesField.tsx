import { Flex, Select, SelectProps, Tag, Text } from "fidesui";
import { ReactNode, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import DataCategorySelect from "~/features/common/dropdown/DataCategorySelect";
import DataSubjectSelect from "~/features/common/dropdown/DataSubjectSelect";
import DataUseSelect from "~/features/common/dropdown/DataUseSelect";
import SystemGroupSelect from "~/features/common/dropdown/SystemGroupSelect";
import useTaxonomies from "~/features/common/hooks/useTaxonomies";
import {
  selectSystemGroupsAsTaxonomyEntities,
  useGetAllSystemGroupsQuery,
} from "~/features/system/system-groups.slice";
import CustomTaxonomySelect from "~/features/taxonomy/components/CustomTaxonomySelect";
import { useGetTaxonomyQuery } from "~/features/taxonomy/taxonomy.slice";

import { BUILT_IN_TAXONOMY_KEYS, ConditionProperty } from "./types";

interface ConditionValuesFieldProps {
  property: string | undefined;
  values: string[] | undefined;
  onChange: (values: string[]) => void;
}

const ConditionValuesField = ({
  property,
  values,
  onChange,
}: ConditionValuesFieldProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const {
    getDataUseDisplayName,
    getDataCategoryDisplayName,
    getDataSubjectDisplayName,
  } = useTaxonomies();

  useGetAllSystemGroupsQuery();
  const systemGroups = useAppSelector(selectSystemGroupsAsTaxonomyEntities);

  const isCustomTaxonomy =
    !!property &&
    !BUILT_IN_TAXONOMY_KEYS.includes(property as ConditionProperty);
  const { data: customTaxonomyItems = [] } = useGetTaxonomyQuery(
    property ?? "",
    { skip: !isCustomTaxonomy },
  );

  if (!property) {
    return (
      <Select
        disabled
        placeholder="Select a taxonomy first"
        className="w-full"
        aria-label="Select values"
        data-testid="condition-values-disabled"
      />
    );
  }

  const safeValues = values ?? [];

  const getDisplayName = (value: string): ReactNode => {
    switch (property) {
      case ConditionProperty.DATA_USE:
        return getDataUseDisplayName(value);
      case ConditionProperty.DATA_CATEGORIES:
        return getDataCategoryDisplayName(value);
      case ConditionProperty.DATA_SUBJECTS:
        return getDataSubjectDisplayName(value);
      case ConditionProperty.SYSTEM_GROUP: {
        const group = systemGroups.find((g) => g.fides_key === value);
        return group?.name ?? value;
      }
      default: {
        const item = customTaxonomyItems.find((t) => t.fides_key === value);
        return item?.name ?? value;
      }
    }
  };

  if (isEditing) {
    const renderSelectedTag: SelectProps["tagRender"] = ({
      value,
      closable,
      onClose,
    }) => (
      <Tag
        color="white"
        closable={closable}
        onClose={onClose}
        onMouseDown={(e) => {
          e.preventDefault();
          e.stopPropagation();
        }}
        style={{
          marginInlineEnd: "var(--fidesui-padding-xs)",
          marginBottom: "var(--fidesui-padding-xs)",
        }}
      >
        <Text
          ellipsis={{ tooltip: true }}
          style={{ color: "inherit", maxWidth: 200 }}
        >
          {getDisplayName(value as string)}
        </Text>
      </Tag>
    );

    const commonProps = {
      selectedTaxonomies: safeValues,
      value: safeValues,
      onChange: (v: unknown) => onChange(v as string[]),
      mode: "multiple" as const,
      autoFocus: true,
      open: true,
      onBlur: () => setIsEditing(false),
      tagRender: renderSelectedTag,
    };

    switch (property) {
      case ConditionProperty.DATA_USE:
        return (
          <DataUseSelect
            {...commonProps}
            placeholder="Select data uses"
            data-testid="condition-values-data-use"
          />
        );
      case ConditionProperty.DATA_CATEGORIES:
        return (
          <DataCategorySelect
            {...commonProps}
            placeholder="Select data categories"
            data-testid="condition-values-data-category"
          />
        );
      case ConditionProperty.DATA_SUBJECTS:
        return (
          <DataSubjectSelect
            {...commonProps}
            placeholder="Select data subjects"
            data-testid="condition-values-data-subject"
          />
        );
      case ConditionProperty.SYSTEM_GROUP:
        return (
          <SystemGroupSelect
            {...commonProps}
            placeholder="Select system groups"
            data-testid="condition-values-system-group"
          />
        );
      default:
        return (
          <CustomTaxonomySelect
            {...commonProps}
            taxonomyKey={property}
            placeholder="Select values"
            data-testid="condition-values-custom"
          />
        );
    }
  }

  return (
    <Flex wrap gap="small" align="center" data-testid="condition-values-chips">
      {safeValues.map((value) => (
        <Tag
          key={value}
          color="white"
          closable
          onClose={() => onChange(safeValues.filter((v) => v !== value))}
          closeButtonLabel="Remove value"
          data-testid={`condition-value-${value}`}
        >
          <Text
            ellipsis={{ tooltip: true }}
            style={{ color: "inherit", maxWidth: 200 }}
          >
            {getDisplayName(value)}
          </Text>
        </Tag>
      ))}
      <Tag
        addable
        onClick={() => setIsEditing(true)}
        aria-label="Add value"
        data-testid="condition-values-add-btn"
      />
    </Flex>
  );
};

export default ConditionValuesField;
