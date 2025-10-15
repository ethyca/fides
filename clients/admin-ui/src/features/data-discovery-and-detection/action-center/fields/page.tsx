import {
  AntButton as Button,
  AntDropdown as Dropdown,
  AntFlex as Flex,
  AntList as List,
  AntPagination as Pagination,
  AntSplitter as Splitter,
  AntText as Text,
  AntTitle as Title,
  Icons,
  useToast,
} from "fidesui";
import { NextPage } from "next";
import { useRouter } from "next/router";
import { Key, useEffect, useState } from "react";

import { DebouncedSearchInput } from "~/features/common/DebouncedSearchInput";
import FixedLayout from "~/features/common/FixedLayout";
import { getErrorMessage } from "~/features/common/helpers";
import { useAlert, useSearch } from "~/features/common/hooks";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import { useAntPagination } from "~/features/common/pagination/useAntPagination";
import { errorToastParams, successToastParams } from "~/features/common/toast";
import {
  useClassifyStagedResourcesMutation,
  useGetMonitorConfigQuery,
  useGetMonitorFieldsQuery,
  useIgnoreMonitorResultAssetsMutation,
} from "~/features/data-discovery-and-detection/action-center/action-center.slice";
import {
  usePromoteResourcesMutation,
  useUpdateResourceCategoryMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { DiffStatus } from "~/types/api";
import { isErrorResult } from "~/types/errors";

import { MonitorFieldFilters } from "./MonitorFieldFilters";
import renderMonitorFieldListItem from "./MonitorFieldListItem";
import MonitorTree from "./MonitorTree";
import { RESOURCE_STATUS, useMonitorFieldsFilters } from "./useFilters";

const FIELD_PAGE_SIZE = 25;

type ResourceStatusLabel = (typeof RESOURCE_STATUS)[number];
type ResourceStatusLabelColor = "nectar" | "red" | "orange" | "blue" | "green";

const ResourceStatus: Record<
  DiffStatus,
  {
    label: ResourceStatusLabel;
    color?: ResourceStatusLabelColor;
  }
> = {
  classifying: { label: "Classifying", color: "blue" },
  classification_queued: { label: "Classifying", color: "blue" },
  classification_update: { label: "In Review", color: "nectar" },
  classification_addition: { label: "In Review", color: "blue" },
  addition: { label: "Attention Required", color: "blue" },
  muted: { label: "Unmonitored", color: "nectar" },
  removal: { label: "Removed", color: "red" },
  removing: { label: "In Review", color: "nectar" },
  promoting: { label: "In Review", color: "nectar" },
  monitored: { label: "Confirmed", color: "nectar" },
  approved: { label: "Approved", color: "green" },
} as const;

const intoDiffStatus = (resourceStatusLabel: ResourceStatusLabel) =>
  Object.values(DiffStatus).flatMap((status) =>
    ResourceStatus[status].label === resourceStatusLabel ? [status] : [],
  );

const ActionCenterFields: NextPage = () => {
  const router = useRouter();
  const monitorId = decodeURIComponent(router.query.monitorId as string);
  const { paginationProps, pageIndex, pageSize, resetPagination } =
    useAntPagination({
      defaultPageSize: FIELD_PAGE_SIZE,
    });
  const search = useSearch();
  const {
    resourceStatus,
    confidenceScore,
    dataCategory,
    ...restMonitorFieldsFilters
  } = useMonitorFieldsFilters();
  const { data: monitorConfigData } = useGetMonitorConfigQuery({
    monitor_config_id: monitorId,
  });
  const [selectedNodeKeys, setSelectedNodeKeys] = useState<Key[]>([]);
  const [selectedFields, setSelectedFields] = useState<string[]>([]);
  const { data: fieldsDataResponse } = useGetMonitorFieldsQuery({
    monitor_config_id: monitorId,
    size: pageSize,
    page: pageIndex,
    staged_resource_urn: selectedNodeKeys.map((key) => key.toString()),
    search: search.searchProps.value,
    diff_status: resourceStatus
      ? resourceStatus.flatMap(intoDiffStatus)
      : undefined,
    confidence_score: confidenceScore || undefined,
    data_category: dataCategory || undefined,
  });
  const toast = useToast();
  const [classifyStagedResourcesMutation] =
    useClassifyStagedResourcesMutation();
  const [updateResourceCategoryMutation] = useUpdateResourceCategoryMutation();
  const [ignoreMonitorResultAssetsMutation] =
    useIgnoreMonitorResultAssetsMutation();
  const { errorAlert } = useAlert();
  const [promoteResources] = usePromoteResourcesMutation();

  const handleSetDataUses = async (dataUses: string[], urn: string) => {
    const mutationResult = await updateResourceCategoryMutation({
      monitor_config_id: monitorId,
      staged_resource_urn: urn,
      user_assigned_data_categories: dataUses,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
    }
  };

  const handleIgnore = async (urn: string) => {
    const mutationResult = await ignoreMonitorResultAssetsMutation({
      urnList: [urn],
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
    }
  };

  const handlePromote = async (urns: string[]) => {
    const mutationResult = await promoteResources({
      staged_resource_urns: urns,
    });

    if (isErrorResult(mutationResult)) {
      errorAlert(getErrorMessage(mutationResult.error));
    }
  };

  const handleClassifyStagedResources = async () => {
    const result = await classifyStagedResourcesMutation({
      monitor_config_key: monitorId,
      staged_resource_urns: selectedNodeKeys.flatMap((key) =>
        typeof key !== "bigint" ? [key.toString()] : [],
      ),
    });

    if (isErrorResult(result)) {
      toast(errorToastParams(getErrorMessage(result.error)));
      return;
    }

    toast(successToastParams(`Classifying initiated`));
  };
  /**
   * @todo: this should be handled on a form/state action level
   */
  useEffect(() => {
    resetPagination();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    resourceStatus,
    confidenceScore,
    selectedNodeKeys,
    search.searchQuery,
    dataCategory,
  ]);

  return (
    <FixedLayout
      title="Action center - Discovered assets by system"
      mainProps={{ overflow: "hidden" }}
    >
      <PageHeader
        heading="Action center"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          { title: monitorId },
        ]}
        isSticky={false}
      />
      <Splitter className="h-[calc(100%-48px)] overflow-hidden">
        <Splitter.Panel
          defaultSize={250}
          /** Note: style attr used here due to specificity of ant css. */
          style={{ paddingRight: "var(--ant-padding-md)" }}
        >
          <MonitorTree
            selectedNodeKeys={selectedNodeKeys}
            setSelectedNodeKeys={setSelectedNodeKeys}
            onClickClassifyButton={handleClassifyStagedResources}
          />
        </Splitter.Panel>
        {/** Note: style attr used here due to specificity of ant css. */}
        <Splitter.Panel style={{ paddingLeft: "var(--ant-padding-md)" }}>
          <Flex vertical gap="middle" className="h-full overflow-hidden">
            <Flex justify="space-between">
              <Title level={2}>Monitor results</Title>
              <Flex align="center">
                {monitorConfigData?.last_monitored && (
                  <Text type="secondary">
                    Last scan:{" "}
                    {new Date(
                      monitorConfigData?.last_monitored,
                    ).toLocaleString()}
                  </Text>
                )}
              </Flex>
            </Flex>

            <Flex justify="space-between">
              <DebouncedSearchInput
                value={search.searchQuery}
                onChange={search.updateSearch}
                placeholder="Search"
              />
              <Flex gap="small">
                <Dropdown
                  trigger={["click"]}
                  /* I don't like disabling linting but this pattern is inherit to ant-d */
                  /* eslint-disable-next-line react/no-unstable-nested-components */
                  popupRender={() => (
                    <MonitorFieldFilters
                      resourceStatus={resourceStatus}
                      confidenceScore={confidenceScore}
                      dataCategory={dataCategory}
                      {...restMonitorFieldsFilters}
                      monitorId={monitorId}
                    />
                  )}
                >
                  <Button icon={<Icons.ChevronDown />} iconPosition="end">
                    Filter
                  </Button>
                </Dropdown>
                <Dropdown
                  menu={{
                    items: [
                      {
                        key: "promote",
                        onClick: () => handlePromote(selectedFields),
                        label: "Promote",
                      },
                    ],
                  }}
                  disabled={selectedFields.length <= 0}
                >
                  <Button
                    type="primary"
                    icon={<Icons.ChevronDown />}
                    iconPosition="end"
                  >
                    Actions
                  </Button>
                </Dropdown>
              </Flex>
            </Flex>
            <List
              dataSource={fieldsDataResponse?.items}
              className="overflow-scroll"
              renderItem={(props) =>
                renderMonitorFieldListItem({
                  ...props,
                  selected: selectedFields.includes(props.urn),
                  onSelect: (key, selected) =>
                    selected
                      ? setSelectedFields([...selectedFields, key])
                      : setSelectedFields(
                          selectedFields.filter((val) => val !== key),
                        ),
                  onSetDataUses: handleSetDataUses,
                  onIgnore: handleIgnore,
                })
              }
            />
            <Pagination
              {...paginationProps}
              showSizeChanger={false}
              total={fieldsDataResponse?.total || 0}
            />
          </Flex>
        </Splitter.Panel>
      </Splitter>
    </FixedLayout>
  );
};

export default ActionCenterFields;
