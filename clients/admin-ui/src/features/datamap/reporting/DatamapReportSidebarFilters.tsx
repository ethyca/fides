import { Select, Typography } from "fidesui";
import { useMemo } from "react";

import { useAppSelector } from "~/app/hooks";
import {
  selectDataSubjects,
  useGetAllDataSubjectsQuery,
} from "~/features/data-subjects/data-subject.slice";
import {
  selectDataUses,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import {
  selectDataCategories,
  useGetAllDataCategoriesQuery,
} from "~/features/taxonomy/data-category.slice";

import { DatamapReportFilterSelections } from "../types";

const { Text } = Typography;

interface SelectOption {
  label: string;
  value: string;
}

const flattenTaxonomyEntities = (
  entities: Array<{ fides_key: string; name?: string | null }>,
): SelectOption[] =>
  entities.map((entity) => ({
    label: entity.name || entity.fides_key,
    value: entity.fides_key,
  }));

interface DatamapReportSidebarFiltersProps {
  selectedFilters: DatamapReportFilterSelections;
  onFilterChange: (filters: DatamapReportFilterSelections) => void;
}

const DatamapReportSidebarFilters = ({
  selectedFilters,
  onFilterChange,
}: DatamapReportSidebarFiltersProps) => {
  useGetAllDataUsesQuery();
  useGetAllDataSubjectsQuery();
  useGetAllDataCategoriesQuery();

  const dataUses = useAppSelector(selectDataUses);
  const dataSubjects = useAppSelector(selectDataSubjects);
  const dataCategories = useAppSelector(selectDataCategories);

  const dataUseOptions = useMemo(
    () => flattenTaxonomyEntities(dataUses),
    [dataUses],
  );
  const dataSubjectOptions = useMemo(
    () => flattenTaxonomyEntities(dataSubjects),
    [dataSubjects],
  );
  const dataCategoryOptions = useMemo(
    () => flattenTaxonomyEntities(dataCategories),
    [dataCategories],
  );

  return (
    <>
      <div>
        <Text type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
          Data uses
        </Text>
        <Select
          mode="multiple"
          allowClear
          placeholder="All data uses"
          options={dataUseOptions}
          value={selectedFilters.dataUses}
          onChange={(values) =>
            onFilterChange({ ...selectedFilters, dataUses: values })
          }
          style={{ width: "100%" }}
          maxTagCount="responsive"
          data-testid="datamap-filter-data-uses"
        />
      </div>
      <div>
        <Text type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
          Data categories
        </Text>
        <Select
          mode="multiple"
          allowClear
          placeholder="All data categories"
          options={dataCategoryOptions}
          value={selectedFilters.dataCategories}
          onChange={(values) =>
            onFilterChange({ ...selectedFilters, dataCategories: values })
          }
          style={{ width: "100%" }}
          maxTagCount="responsive"
          data-testid="datamap-filter-data-categories"
        />
      </div>
      <div>
        <Text type="secondary" style={{ fontSize: 12, marginBottom: 4 }}>
          Data subjects
        </Text>
        <Select
          mode="multiple"
          allowClear
          placeholder="All data subjects"
          options={dataSubjectOptions}
          value={selectedFilters.dataSubjects}
          onChange={(values) =>
            onFilterChange({ ...selectedFilters, dataSubjects: values })
          }
          style={{ width: "100%" }}
          maxTagCount="responsive"
          data-testid="datamap-filter-data-subjects"
        />
      </div>
    </>
  );
};

export default DatamapReportSidebarFilters;
