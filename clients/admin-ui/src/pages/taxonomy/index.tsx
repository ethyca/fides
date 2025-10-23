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

import { useFeatures } from "~/features/common/features";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useHasPermission } from "~/features/common/Restrict";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import TaxonomyEditDrawer from "~/features/taxonomy/components/TaxonomyEditDrawer";
import TaxonomyInteractiveTree from "~/features/taxonomy/components/TaxonomyInteractiveTree";
import {
  CoreTaxonomiesEnum,
  TAXONOMY_ROOT_NODE_ID,
  taxonomyKeyToScopeRegistryEnum,
  TaxonomyTypeEnum,
} from "~/features/taxonomy/constants";
import useTaxonomySlices from "~/features/taxonomy/hooks/useTaxonomySlices";
import { useGetCustomTaxonomiesQuery } from "~/features/taxonomy/taxonomy.slice";
import { TaxonomyEntity } from "~/features/taxonomy/types";

const TaxonomyPage: NextPage = () => {
  // taxonomyType now stores the fides_key string (e.g. "data_category")
  const [taxonomyType, setTaxonomyType] = useState<string>(
    TaxonomyTypeEnum.DATA_CATEGORY,
  );
  const features = useFeatures();
  const isPlusEnabled = features.plus;
  const { data: customTaxonomies } = useGetCustomTaxonomiesQuery(undefined, {
    skip: !isPlusEnabled,
  });
  const {
    createTrigger,
    getAllTrigger,
    taxonomyItems = [],
    isCreating,
  } = useTaxonomySlices({ taxonomyType });
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

  // Redirect away from system groups if Plus is disabled
  useEffect(() => {
    if (taxonomyType === TaxonomyTypeEnum.SYSTEM_GROUP && !isPlusEnabled) {
      setTaxonomyType(TaxonomyTypeEnum.DATA_CATEGORY);
    }
  }, [taxonomyType, isPlusEnabled]);

  const toast = useToast();
  const createNewLabel = useCallback(
    async (labelName: string) => {
      if (!draftNewItem) {
        return;
      }

      const isChildOfRoot = draftNewItem?.parent_key === TAXONOMY_ROOT_NODE_ID;
      const newItem = {
        ...draftNewItem,
        name: labelName,
        parent_key: isChildOfRoot ? null : draftNewItem.parent_key,
      };

      const result = await createTrigger(newItem);
      if (isErrorResult(result)) {
        toast(errorToastParams(getErrorMessage(result.error)));
        return;
      }
      setLastCreatedItemKey(result.data.fides_key);
      toast(successToastParams("New label successfully created"));
      setDraftNewItem(null);
    },
    [createTrigger, draftNewItem, toast],
  );

  const activeTaxonomyItems = filter(
    taxonomyItems,
    "active",
  ) as TaxonomyEntity[];

  const userCanAddLabels = useHasPermission([
    taxonomyKeyToScopeRegistryEnum(taxonomyType).CREATE,
  ]);

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
              onSelect={({ key }) => setTaxonomyType(key as string)}
              items={(() => {
                // Core taxonomies, excluding system groups if plus is not enabled
                const coreMapping: Record<CoreTaxonomiesEnum, string> = {
                  [CoreTaxonomiesEnum.DATA_CATEGORIES]:
                    TaxonomyTypeEnum.DATA_CATEGORY,
                  [CoreTaxonomiesEnum.DATA_USES]: TaxonomyTypeEnum.DATA_USE,
                  [CoreTaxonomiesEnum.DATA_SUBJECTS]:
                    TaxonomyTypeEnum.DATA_SUBJECT,
                  [CoreTaxonomiesEnum.SYSTEM_GROUPS]:
                    TaxonomyTypeEnum.SYSTEM_GROUP,
                };

                const items = enumToOptions(CoreTaxonomiesEnum)
                  .filter(
                    (opt) =>
                      isPlusEnabled ||
                      opt.value !== CoreTaxonomiesEnum.SYSTEM_GROUPS,
                  )
                  .map((e) => ({
                    label: e.label,
                    key: coreMapping[e.value as CoreTaxonomiesEnum],
                  }));

                // Custom taxonomies, if available
                if (customTaxonomies?.length) {
                  customTaxonomies.forEach((t) => {
                    items.push({ label: t.name, key: t.fides_key as any });
                  });
                }

                return items;
              })()}
              data-testid="taxonomy-type-selector"
            />
          </div>

          {!!taxonomyItems.length && (
            <TaxonomyInteractiveTree
              userCanAddLabels={userCanAddLabels}
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
              taxonomyType={taxonomyType as any}
              onCancelDraftItem={() => setDraftNewItem(null)}
              onSubmitDraftItem={createNewLabel}
              isCreating={isCreating}
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
