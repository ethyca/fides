import { AntButton, AntInput, AntSelect, AntSpace, useToast } from "fidesui";
import type { NextPage } from "next";
import { useCallback, useEffect, useState } from "react";

import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import TaxonomyEditDrawer from "~/features/taxonomy/components/TaxonomyEditDrawer";
import TaxonomyInteractiveTree from "~/features/taxonomy/components/TaxonomyInteractiveTree";
import useTaxonomySlices from "~/features/taxonomy/hooks/useTaxonomySlices";
import { TaxonomyEntity } from "~/features/taxonomy/types";
import { CoreTaxonomiesEnum } from "~/features/taxonomy/types/CoreTaxonomiesEnum";

const TaxonomyPage: NextPage = () => {
  const [taxonomyType, setTaxonomyType] = useState<CoreTaxonomiesEnum>(
    CoreTaxonomiesEnum.DATA_CATEGORIES,
  );
  const { createTrigger, getAllTrigger, taxonomyItems } = useTaxonomySlices({
    taxonomyType,
  });

  useEffect(() => {
    getAllTrigger();
  }, [getAllTrigger, taxonomyType]);

  const [taxonomyItemToEdit, setTaxonomyItemToEdit] =
    useState<TaxonomyEntity | null>(null);

  const [draftNewItem, setDraftNewItem] =
    useState<Partial<TaxonomyEntity> | null>(null);

  // reset state when changing taxonomy type
  useEffect(() => {
    setDraftNewItem(null);
    setTaxonomyItemToEdit(null);
  }, [taxonomyType]);

  const toast = useToast();
  const createNewLabel = useCallback(
    async (labelName: string) => {
      if (!draftNewItem) {
        return;
      }

      // defer LA-41: remove fides_key from request, be will autogenerate it
      let fidesKey;
      if (draftNewItem.parent_key) {
        fidesKey = `${draftNewItem.parent_key}.${labelName.toLocaleLowerCase().replaceAll(" ", "_")}`;
      } else {
        fidesKey = labelName.toLocaleLowerCase().replaceAll(" ", "_");
      }

      const newItem = {
        ...draftNewItem,
        name: labelName,
        fides_key: fidesKey,
      };

      const result = await createTrigger(newItem);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }
      toast(successToastParams("New label successfully created"));
      setDraftNewItem(null);
    },
    [createTrigger, draftNewItem, toast],
  );

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
            onCancelDraftItem={() => setDraftNewItem(null)}
            onSubmitDraftItem={createNewLabel}
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
