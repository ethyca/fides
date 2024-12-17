import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntSpace as Space,
  FloatingMenu,
  useToast,
} from "fidesui";
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
import { CoreTaxonomiesEnum } from "~/features/taxonomy/constants";
import useTaxonomySlices from "~/features/taxonomy/hooks/useTaxonomySlices";
import { TaxonomyEntity } from "~/features/taxonomy/types";

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

  const [lastCreatedItemKey, setLastCreatedItemKey] = useState<string | null>(
    null,
  );

  // reset state when changing taxonomy type
  useEffect(() => {
    setDraftNewItem(null);
    setLastCreatedItemKey(null);
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
      setLastCreatedItemKey(result.data.fides_key);
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
    <Layout title="Taxonomy">
      <Flex vertical className="h-full">
        <div>
          <PageHeader heading="Taxonomy" />

          {/* hide search bar until functionality is implemented */}
          <div className="hidden">
            <div className="mb-5 flex justify-between">
              <Space.Compact>
                <Input
                  className="min-w-[350px]"
                  placeholder="Search"
                  allowClear
                />
                <Button type="default">Clear</Button>
              </Space.Compact>
            </div>
          </div>
        </div>
        <div className="relative grow">
          <div className="absolute left-2 top-2 z-[1]">
            <FloatingMenu
              selectedKeys={[taxonomyType]}
              onSelect={({ key }) => setTaxonomyType(key as CoreTaxonomiesEnum)}
              items={enumToOptions(CoreTaxonomiesEnum).map((e) => ({
                label: e.label,
                key: e.value,
              }))}
              data-testid="taxonomy-type-selector"
            />
          </div>

          {!!taxonomyItems.length && (
            <TaxonomyInteractiveTree
              taxonomyItems={
                showDisabledItems ? taxonomyItems : activeTaxonomyItems
              }
              draftNewItem={draftNewItem}
              lastCreatedItemKey={lastCreatedItemKey}
              resetLastCreatedItemKey={() => setLastCreatedItemKey(null)}
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
      </Flex>
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
