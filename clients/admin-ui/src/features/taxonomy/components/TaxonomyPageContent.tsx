import {
  AntButton as Button,
  AntFlex as Flex,
  AntInput as Input,
  AntMenuProps as MenuProps,
  AntModal as Modal,
  AntSpace as Space,
  AntTypography as Typography,
  FloatingMenu,
  useAntModal,
  useMessage,
} from "fidesui";
import { filter } from "lodash";
import { useRouter } from "next/router";
import { useCallback, useEffect, useMemo, useState } from "react";

import { useFeatures } from "~/features/common/features";
import {
  enumToOptions,
  getErrorMessage,
  isErrorResult,
} from "~/features/common/helpers";
import Layout from "~/features/common/Layout";
import PageHeader from "~/features/common/PageHeader";
import { useHasPermission } from "~/features/common/Restrict";
import { useGetHealthQuery } from "~/features/plus/plus.slice";
import CreateCustomTaxonomyForm from "~/features/taxonomy/components/CreateCustomTaxonomyForm";
import CustomTaxonomyEditDrawer from "~/features/taxonomy/components/CustomTaxonomyEditDrawer";
import TaxonomyItemEditDrawer from "~/features/taxonomy/components/TaxonomyEditDrawer";
import TaxonomyInteractiveTree from "~/features/taxonomy/components/TaxonomyInteractiveTree";
import {
  CoreTaxonomiesEnum,
  TAXONOMY_ROOT_NODE_ID,
  taxonomyKeyToScopeRegistryEnum,
  TaxonomyTypeEnum,
  taxonomyTypeToLabel,
} from "~/features/taxonomy/constants";
import useTaxonomySlices from "~/features/taxonomy/hooks/useTaxonomySlices";
import {
  useDeleteCustomTaxonomyMutation,
  useGetCustomTaxonomiesQuery,
} from "~/features/taxonomy/taxonomy.slice";
import { TaxonomyEntity } from "~/features/taxonomy/types";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";

// include spaces to avoid collision with taxonomy fides_keys
const ADD_NEW_ITEM_KEY = "add new item";

const DEFAULT_TAXONOMY_TYPE = TaxonomyTypeEnum.DATA_CATEGORY;

interface TaxonomyPageContentProps {
  initialTaxonomy?: string;
}

const TaxonomyPageContent = ({ initialTaxonomy }: TaxonomyPageContentProps) => {
  const router = useRouter();
  const [taxonomyType, setTaxonomyType] = useState<string>(
    initialTaxonomy || DEFAULT_TAXONOMY_TYPE,
  );

  const isCustomTaxonomy = !Object.values(TaxonomyTypeEnum).includes(
    taxonomyType as TaxonomyTypeEnum,
  );
  const features = useFeatures();
  const isPlusEnabled = features.plus;
  const { isLoading: isPlusHealthLoading } = useGetHealthQuery();
  const { data: customTaxonomies } = useGetCustomTaxonomiesQuery(undefined, {
    skip: !isPlusEnabled,
  });

  // Sync taxonomyType when initialTaxonomy changes (after router hydration)
  useEffect(() => {
    if (initialTaxonomy) {
      setTaxonomyType(initialTaxonomy);
    }
  }, [initialTaxonomy]);

  const {
    createTrigger,
    getAllTrigger,
    taxonomyItems = [],
    isCreating,
  } = useTaxonomySlices({ taxonomyType });
  const showDisabledItems = router.query.showDisabledItems === "true";

  const messageApi = useMessage();

  useEffect(() => {
    getAllTrigger();
  }, [getAllTrigger, taxonomyType]);

  const [taxonomyItemToEdit, setTaxonomyItemToEdit] =
    useState<TaxonomyEntity | null>(null);
  const [taxonomyTypeToEdit, setTaxonomyTypeToEdit] =
    useState<TaxonomyResponse | null>(null);

  const [draftNewItem, setDraftNewItem] =
    useState<Partial<TaxonomyEntity> | null>(null);

  const [lastCreatedItemKey, setLastCreatedItemKey] = useState<string | null>(
    null,
  );

  const modal = useAntModal();

  const [deleteCustomTaxonomy] = useDeleteCustomTaxonomyMutation();

  const handleDelete = async () => {
    if (!taxonomyTypeToEdit?.fides_key) {
      messageApi.error("Taxonomy not found");
      return;
    }
    const result = await deleteCustomTaxonomy(taxonomyTypeToEdit.fides_key);
    if (isErrorResult(result)) {
      messageApi.error(getErrorMessage(result.error));
      return;
    }
    messageApi.success("Taxonomy deleted successfully");
    setTaxonomyTypeToEdit(null);
    // Navigate to index page after deletion, preserving query parameters
    const query = { ...router.query };
    delete query.key;
    router.replace(
      {
        pathname: "/taxonomy",
        query,
      },
      undefined,
      { shallow: true },
    );
  };

  const confirmDelete = () => {
    modal.confirm({
      title: `Delete ${taxonomyTypeToEdit?.name}?`,
      icon: null,
      content: (
        <Typography.Paragraph>
          Are you sure you want to delete this taxonomy? This action cannot be
          undone.
        </Typography.Paragraph>
      ),
      okText: "Delete",
      okType: "primary",
      onOk: handleDelete,
      centered: true,
    });
  };

  const customTaxonomyLabel = useMemo(() => {
    if (!customTaxonomies) {
      return null;
    }
    const customTaxonomyResponse = customTaxonomies.find(
      (t) => t.fides_key === taxonomyType,
    );
    return customTaxonomyResponse?.name ?? customTaxonomyResponse?.fides_key;
  }, [customTaxonomies, taxonomyType]);

  const [isAddNewItemModalOpen, setIsAddNewItemModalOpen] = useState(false);

  // reset state when changing taxonomy type
  useEffect(() => {
    setDraftNewItem(null);
    setLastCreatedItemKey(null);
    setTaxonomyItemToEdit(null);
  }, [taxonomyType]);

  // Redirect away from system groups if Plus is disabled
  useEffect(() => {
    if (
      taxonomyType === TaxonomyTypeEnum.SYSTEM_GROUP &&
      !isPlusHealthLoading &&
      !isPlusEnabled
    ) {
      const query = { ...router.query };
      delete query.key;
      router.replace(
        {
          pathname: "/taxonomy",
          query,
        },
        undefined,
        { shallow: true },
      );
    }
  }, [taxonomyType, isPlusEnabled, isPlusHealthLoading, router]);

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
        messageApi.error(getErrorMessage(result.error));
        return;
      }
      setLastCreatedItemKey(result.data.fides_key);
      messageApi.success("New label successfully created");
      setDraftNewItem(null);
    },
    [createTrigger, draftNewItem, messageApi],
  );

  const activeTaxonomyItems = filter(
    taxonomyItems,
    "active",
  ) as TaxonomyEntity[];

  const userCanAddLabels = useHasPermission([
    taxonomyKeyToScopeRegistryEnum(taxonomyType).CREATE,
  ]);

  const handleMenuItemSelected = ({ key }: { key: string }) => {
    if (key === ADD_NEW_ITEM_KEY) {
      setIsAddNewItemModalOpen(true);
      return;
    }
    // Update URL when taxonomy changes, preserving query parameters
    const query = { ...router.query };
    delete query.key;
    router.replace(
      {
        pathname: `/taxonomy/${key}`,
        query,
      },
      undefined,
      { shallow: true },
    );
    setTaxonomyType(key);
  };

  const handleTaxonomyRootItemClick = () => {
    const typeFromKey = customTaxonomies?.find(
      (t) => t.fides_key === taxonomyType,
    );
    if (!typeFromKey) {
      return;
    }
    setTaxonomyTypeToEdit(typeFromKey);
  };

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
              onSelect={handleMenuItemSelected}
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

                const items: MenuProps["items"] = enumToOptions(
                  CoreTaxonomiesEnum,
                )
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
                if (isPlusEnabled) {
                  items.push({ type: "divider" });
                  items.push({
                    label: "+ Create new",
                    key: ADD_NEW_ITEM_KEY,
                  });
                }

                return items;
              })()}
              data-testid="taxonomy-type-selector"
            />
          </div>

          <Modal
            open={isAddNewItemModalOpen}
            destroyOnHidden
            onCancel={() => setIsAddNewItemModalOpen(false)}
            width={768}
            footer={null}
            centered
            title="Create new taxonomy"
          >
            <CreateCustomTaxonomyForm
              onClose={() => setIsAddNewItemModalOpen(false)}
            />
          </Modal>

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
            onRootItemClick={
              isCustomTaxonomy ? handleTaxonomyRootItemClick : null
            }
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
            rootNodeLabel={
              customTaxonomyLabel ??
              taxonomyTypeToLabel(taxonomyType as TaxonomyTypeEnum)
            }
          />
        </div>
      </Flex>
      {taxonomyItemToEdit && (
        <TaxonomyItemEditDrawer
          taxonomyItem={taxonomyItemToEdit}
          taxonomyType={taxonomyType}
          onClose={() => setTaxonomyItemToEdit(null)}
        />
      )}
      {isPlusEnabled && taxonomyTypeToEdit && (
        <CustomTaxonomyEditDrawer
          title={
            customTaxonomyLabel
              ? `Edit ${customTaxonomyLabel}`
              : "Edit taxonomy"
          }
          onClose={() => setTaxonomyTypeToEdit(null)}
          onDelete={confirmDelete}
          taxonomy={taxonomyTypeToEdit}
        />
      )}
    </Layout>
  );
};

export default TaxonomyPageContent;
