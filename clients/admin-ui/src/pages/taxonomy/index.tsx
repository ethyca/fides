import { AntButton, AntInput, AntSelect, AntSpace } from "fidesui";
import type { NextPage } from "next";
import { useEffect, useState } from "react";

import { enumToOptions } from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import TaxonomyEditDrawer from "~/features/taxonomy/components/TaxonomyEditDrawer";
import TaxonomyInteractiveTree from "~/features/taxonomy/components/TaxonomyInteractiveTree";
import useTaxonomy from "~/features/taxonomy/hooks/useTaxonomy";
import { TaxonomyEntity } from "~/features/taxonomy/types";
import { CoreTaxonomiesEnum } from "~/features/taxonomy/types/CoreTaxonomiesEnum";

const TaxonomyPage: NextPage = () => {
  const [taxonomyType, setTaxonomyType] = useState<CoreTaxonomiesEnum>(
    CoreTaxonomiesEnum.DATA_CATEGORIES,
  );
  const { taxonomyItems } = useTaxonomy({
    taxonomyType,
  });

  const [taxonomyItemToEdit, setTaxonomyItemToEdit] =
    useState<TaxonomyEntity | null>(null);

  const [draftNewItem, setDraftNewItem] =
    useState<Partial<TaxonomyEntity> | null>(null);

  // reset state when changing taxonomy type
  useEffect(() => {
    setDraftNewItem(null);
    setTaxonomyItemToEdit(null);
  }, [taxonomyType]);

  return (
    <Layout
      title="Taxonomy"
      mainProps={{
        padding: "0 40px 48px",
      }}
    >
      <div className="flex h-full flex-col">
        <div>
          <PageHeader breadcrumbs={[{ title: "Taxonomy" }]} />

          <div className="mb-5 flex justify-between">
            <AntSpace.Compact>
              <AntInput
                className="min-w-[350px]"
                placeholder="Search"
                allowClear
              />
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
              options={enumToOptions(CoreTaxonomiesEnum)}
              value={taxonomyType}
            />
          </div>
        </div>
        <div className="grow">
          <TaxonomyInteractiveTree
            taxonomyItems={taxonomyItems || []}
            draftNewItem={draftNewItem}
            onTaxonomyItemClick={(taxonomyItem) => {
              setTaxonomyItemToEdit(taxonomyItem);
            }}
            onAddButtonClick={(taxonomyItem) => {
              const newItem = {
                parent_key: taxonomyItem?.fides_key ?? null,
                is_default: false,
              };

              setDraftNewItem(newItem);
            }}
            taxonomyType={taxonomyType}
          />
        </div>
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
