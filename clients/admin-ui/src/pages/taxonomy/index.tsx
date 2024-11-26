import { AntButton, AntInput, AntMenu, AntSpace, useToast } from "fidesui";
import { filter } from "lodash";
import type { NextPage } from "next";
import { useSearchParams } from "next/navigation";
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
  const {
    createTrigger,
    getAllTrigger,
    taxonomyItems = [],
  } = useTaxonomySlices({
    taxonomyType,
  });
  const searchParams = useSearchParams();
  const showDisabledItems = searchParams?.get("showDisabledItems") === "true";

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
        description: "",
        fides_key: fidesKey,
      };

      const result = await createTrigger(newItem);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }
      toast(successToastParams("New label successfully created"));
      setTimeout(() => setDraftNewItem(null));
    },
    [createTrigger, draftNewItem, toast],
  );

  const activeTaxonomyItems = filter(
    taxonomyItems,
    "active",
  ) as TaxonomyEntity[];

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
          </div>
        </div>
        <div className="relative grow">
          <AntMenu
            style={{ width: 220 }}
            selectedKeys={[taxonomyType]}
            onSelect={({ key }) => setTaxonomyType(key as CoreTaxonomiesEnum)}
            mode="vertical"
            items={enumToOptions(CoreTaxonomiesEnum).map((e) => ({
              label: e.label,
              key: e.value,
            }))}
            className="absolute left-2 top-2 z-[1000]"
          />

          {!!taxonomyItems.length && (
            <TaxonomyInteractiveTree
              taxonomyItems={
                showDisabledItems ? taxonomyItems : activeTaxonomyItems
              }
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
          )}
        </div>
      </div>
      {taxonomyItemToEdit && (
        <TaxonomyEditDrawer
          taxonomyItem={taxonomyItemToEdit}
          taxonomyType={taxonomyType}
          onClose={() => setTaxonomyItemToEdit(null)}
        />
      )}
    </Layout>
  );
};
export default TaxonomyPage;
