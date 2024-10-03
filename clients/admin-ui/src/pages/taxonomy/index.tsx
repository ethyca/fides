import { AntButton, AntInput, AntSelect, AntSpace } from "fidesui";
import type { NextPage } from "next";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useDataCategory } from "~/features/taxonomy/hooks";
import TaxonomyInteractiveFlowVisualization from "~/features/taxonomy/TaxonomyInteractiveFlowVisualization";

const TaxonomyPage: NextPage = () => {
  const {
    isLoading,
    data: taxonomyItems,
    labels,
    entityToEdit,
    setEntityToEdit,
    handleCreate: createEntity,
    handleEdit,
    handleDelete: deleteEntity,
    handleToggleEnabled: toggleEntityEnabled,
    renderExtraFormFields,
    transformEntityToInitialValues,
  } = useDataCategory();

  return (
    <Layout
      title="Taxonomy"
      mainProps={{
        padding: "0 40px 48px",
      }}
    >
      <PageHeader breadcrumbs={[{ title: "Taxonomy" }]} />

      <div className="mb-5 flex justify-between">
        <AntSpace.Compact>
          <AntInput className="min-w-[350px]" placeholder="Search" allowClear />
          <AntButton type="default">Clear</AntButton>
        </AntSpace.Compact>
        <div>
          <AntButton type="primary">Add label</AntButton>
        </div>
      </div>
      <div className="mb-6">
        <AntSelect
          className="min-w-[220px]"
          defaultValue="data_categories"
          style={{ width: 120 }}
          onChange={() => {}}
          options={[
            { value: "data_categories", label: "Data categories" },
            { value: "data_uses", label: "Data uses" },
            { value: "data_subjects", label: "Data subjects" },
          ]}
        />
      </div>
      <div>
        <TaxonomyInteractiveFlowVisualization
          taxonomyItems={taxonomyItems || []}
        />
      </div>
    </Layout>
  );
};
export default TaxonomyPage;
