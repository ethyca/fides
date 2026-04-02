/**
 * Original action center layout with MonitorStats above the content
 * (horizontal card row, no sidebar). Used for A/B comparison.
 */
import {
  Badge,
  BadgeProps,
  Button,
  Dropdown,
  DropdownProps,
  Flex,
  Form,
  Icons,
  Menu,
  Select,
  Tooltip,
} from "fidesui";
import _ from "lodash";
import { PropsWithChildren, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import { useFeatures } from "~/features/common/features";
import FixedLayout from "~/features/common/FixedLayout";
import { ACTION_CENTER_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";
import SearchInput from "~/features/common/SearchInput";
import { formatUser } from "~/features/common/utils";
import useActionCenterNavigation, {
  ActionCenterRoute,
  ActionCenterRouteConfig,
} from "~/features/data-discovery-and-detection/action-center/hooks/useActionCenterNavigation";
import useSearchForm from "~/features/data-discovery-and-detection/action-center/hooks/useSearchForm";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";
import { useGetAllUsersQuery, useGetUserMonitorsQuery } from "~/features/user-management";

import { skipToken } from "@reduxjs/toolkit/query";
import {
  MonitorSearchForm,
  MonitorSearchFormQuerySchema,
  SearchFormQueryState,
} from "./MonitorList.const";
import MonitorStats from "./MonitorStats";
import { SUMMARY_CARD_LABELS } from "./ProgressCard/SummaryCard";

const MONITOR_FILTER_LABEL: Record<MONITOR_TYPES, string> = {
  [MONITOR_TYPES.DATASTORE]:
    SUMMARY_CARD_LABELS.datastore ?? "Connected databases",
  [MONITOR_TYPES.WEBSITE]:
    SUMMARY_CARD_LABELS.website ?? "Tracked websites",
  [MONITOR_TYPES.INFRASTRUCTURE]:
    SUMMARY_CARD_LABELS.infrastructure ?? "Cloud & identity systems",
};

export interface ActionCenterLayoutOriginalProps {
  monitorId?: string;
  routeConfig: ActionCenterRouteConfig;
  pageSettings?: {
    dropdownProps?: DropdownProps;
    badgeProps?: BadgeProps;
  };
  onRefresh?: () => void;
}

const ActionCenterLayoutOriginal = ({
  children,
  monitorId,
  routeConfig,
  pageSettings,
  onRefresh,
}: PropsWithChildren<ActionCenterLayoutOriginalProps>) => {
  const [statsExpanded, setStatsExpanded] = useState(false);
  const {
    flags: { webMonitor: webMonitorEnabled },
  } = useFeatures();
  const {
    items: menuItems,
    activeItem,
    setActiveItem,
  } = useActionCenterNavigation(routeConfig);

  // Search form state (shares nuqs URL params with MonitorList)
  const availableMonitorTypes = [
    ...(webMonitorEnabled ? [MONITOR_TYPES.WEBSITE] : []),
    MONITOR_TYPES.DATASTORE,
    MONITOR_TYPES.INFRASTRUCTURE,
  ] as const;

  const currentUser = useAppSelector(selectUser);
  const { data: userMonitors } = useGetUserMonitorsQuery(
    currentUser?.id ? { id: currentUser.id } : skipToken,
  );
  const defaultStewardFilter =
    (userMonitors ?? []).length > 0 ? currentUser?.id : undefined;

  const { requestData, ...formProps } = useSearchForm<any, MonitorSearchForm>({
    schema: MonitorSearchFormQuerySchema([...availableMonitorTypes]),
    queryState: SearchFormQueryState(
      [...availableMonitorTypes],
      defaultStewardFilter,
    ),
    initialValues: {
      search: null,
      monitor_type: null,
      steward_key: defaultStewardFilter ?? null,
    },
    translate: ({ search, monitor_type, steward_key }) => ({
      search: search || undefined,
      monitor_type: monitor_type
        ? [monitor_type]
        : [...availableMonitorTypes],
      steward_user_id:
        typeof steward_key === "undefined" || !steward_key
          ? []
          : [steward_key],
    }),
  });

  const { data: eligibleUsersData, isLoading: isLoadingUserOptions } =
    useGetAllUsersQuery({
      page: 1,
      size: 100,
      include_external: false,
      exclude_approvers: true,
    });

  const dataStewardOptions = _.uniqBy(
    [
      ...(currentUser
        ? [{ label: "Assigned to me", value: currentUser.id }]
        : []),
      ...(eligibleUsersData?.items || []).map((user) => ({
        label: formatUser(user),
        value: user.id,
      })),
    ],
    "value",
  );

  return (
    <FixedLayout
      title="Action center v2"
      mainProps={{ overflow: "hidden" }}
      fullHeight
    >
      <PageHeader
        heading="Action center v2"
        breadcrumbItems={[
          { title: "All activity", href: ACTION_CENTER_ROUTE },
          ...(monitorId ? [{ title: monitorId }] : []),
        ]}
        isSticky={false}
        rightContent={
          <Flex gap="small">
            {onRefresh && (
              <Tooltip title="Refresh">
                <Button
                  icon={<Icons.Renew />}
                  onClick={onRefresh}
                  aria-label="Refresh"
                />
              </Tooltip>
            )}
            {pageSettings && (
              <Badge {...pageSettings.badgeProps}>
                <Dropdown {...pageSettings.dropdownProps}>
                  <Button
                    aria-label="Page settings"
                    icon={<Icons.SettingsView />}
                  />
                </Dropdown>
              </Badge>
            )}
          </Flex>
        }
      />
      {/* Search/filter bar above widgets */}
      <Form
        {...formProps}
        layout="inline"
        className="mb-4 flex grow gap-2"
      >
        <Flex className="grow justify-between self-stretch">
          <Form.Item name="search" className="self-end">
            <SearchInput />
          </Form.Item>
        </Flex>
        <Form.Item name="monitor_type" className="!me-0 self-end">
          <Select
            options={[...availableMonitorTypes].map((monitorType) => ({
              value: monitorType,
              label: MONITOR_FILTER_LABEL[monitorType],
            }))}
            className="w-auto min-w-[200px]"
            placeholder="Monitor type"
            allowClear
            data-testid="monitor-type-filter"
            aria-label="Filter by monitor type"
          />
        </Form.Item>
        <Form.Item name="steward_key" className="!me-0 self-end">
          <Select
            options={dataStewardOptions}
            loading={isLoadingUserOptions}
            popupMatchSelectWidth
            placeholder="Data steward"
            allowClear
            showSearch
            optionFilterProp="label"
            aria-label="Filter by data steward"
            className="min-w-[220px]"
          />
        </Form.Item>
      </Form>
      <MonitorStats
        monitorId={monitorId}
        layout="top"
        isExpanded={statsExpanded}
        onToggle={() => setStatsExpanded(!statsExpanded)}
      />
      <Menu
        aria-label="Action center tabs"
        mode="horizontal"
        items={Object.values(menuItems)}
        selectedKeys={_.compact([activeItem])}
        onClick={async (menuInfo) => {
          const validKey = Object.values(ActionCenterRoute).find(
            (value) => value === menuInfo.key,
          );
          if (validKey) {
            await setActiveItem(validKey);
          }
        }}
        className="mb-4"
        data-testid="action-center-tabs"
      />
      {children}
    </FixedLayout>
  );
};

export default ActionCenterLayoutOriginal;
