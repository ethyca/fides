import { AntButton, AntInput, AntSelect, AntSpace } from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import TaxonomyEditDrawer from "~/features/taxonomy/components/TaxonomyEditDrawer";
import TaxonomyInteractiveTree from "~/features/taxonomy/components/TaxonomyInteractiveTree";
import useTaxonomy from "~/features/taxonomy/hooks/useTaxonomy";
import { TaxonomyEntity } from "~/features/taxonomy/types";
import { DefaultTaxonomyTypes } from "~/features/taxonomy/types/DefaultTaxonomyTypes";

const TaxonomyPage: NextPage = () => {
  const [taxonomyType, setTaxonomyType] =
    useState<DefaultTaxonomyTypes>("data_categories");
  const { taxonomyItems } = useTaxonomy({
    taxonomyType,
  });

  const [taxonomyItemToEdit, setTaxonomyItemToEdit] =
    useState<TaxonomyEntity | null>(null);

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
          style={{ width: 120 }}
          onChange={(t) => setTaxonomyType(t)}
          options={[
            { value: "data_categories", label: "Data categories" },
            { value: "data_uses", label: "Data uses" },
            { value: "data_subjects", label: "Data subjects" },
          ]}
          value={taxonomyType}
        />
      </div>
      <div>
        <TaxonomyInteractiveTree
          taxonomyItems={taxonomyItems || []}
          onTaxonomyItemClick={(taxonomyItem) => {
            setTaxonomyItemToEdit(taxonomyItem);
          }}
        />
      </div>
      <TaxonomyEditDrawer
        taxonomyItem={taxonomyItemToEdit}
        taxonomyType={taxonomyType}
        onClose={() => setTaxonomyItemToEdit(null)}
      />
    </Layout>
  );
};
export default TaxonomyPage;
