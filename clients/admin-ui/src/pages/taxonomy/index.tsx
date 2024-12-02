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

      const newItem = {
        ...draftNewItem,
        name: labelName,
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

          {/* hide search bar until functionality is implemented */}
          <div className="hidden">
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
        </div>
        <div className="relative grow">
          <div className="absolute left-2 top-2 z-[1000] rounded-md shadow-lg">
            <AntMenu
              className="rounded-md"
              style={{ width: 220 }}
              selectedKeys={[taxonomyType]}
              onSelect={({ key }) => setTaxonomyType(key as CoreTaxonomiesEnum)}
              mode="vertical"
              items={enumToOptions(CoreTaxonomiesEnum).map((e) => ({
                label: e.label,
                key: e.value,
              }))}
            />
          </div>

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
                  description: "",
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
