import { Flex, Form, Select } from "fidesui";
import _ from "lodash";

import { useAppSelector } from "~/app/hooks";
import { selectUser } from "~/features/auth";
import SearchInput from "~/features/common/SearchInput";
import { formatUser } from "~/features/common/utils";
import useSearchForm from "~/features/data-discovery-and-detection/action-center/hooks/useSearchForm";
import { MONITOR_TYPES } from "~/features/data-discovery-and-detection/action-center/utils/getMonitorType";
import { useGetAllUsersQuery } from "~/features/user-management";

import { SearchFormQueryState } from "../MonitorList.const";

const MONITOR_FILTER_LABEL: Record<MONITOR_TYPES, string> = {
  [MONITOR_TYPES.DATASTORE]: "Data store monitors",
  [MONITOR_TYPES.WEBSITE]: "Website monitors",
  [MONITOR_TYPES.INFRASTRUCTURE]: "Infrastructure monitors",
};

const MonitorListSearchForm = ({
  form,
  availableMonitorTypes,
  ...formProps
}: Omit<
  ReturnType<
    typeof useSearchForm<any, ReturnType<typeof SearchFormQueryState>>
  >,
  "requestData"
> & {
  availableMonitorTypes: readonly MONITOR_TYPES[];
}) => {
  const currentUser = useAppSelector(selectUser);

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
        ? [
            {
              label: "Assigned to me",
              value: currentUser.id,
            },
          ]
        : []),
      ...(eligibleUsersData?.items || []).map((user) => ({
        label: formatUser(user),
        value: user.id,
      })),
    ],
    "value",
  );

  return (
    <Form
      form={form}
      {...formProps}
      layout="inline"
      className="flex grow gap-2"
    >
      <Flex className="grow justify-between self-stretch">
        <Form.Item name="search" className="self-end">
          <SearchInput />
        </Form.Item>
      </Flex>
      <Form.Item name="monitor_type" className="!me-0 self-end">
        <Select
          options={availableMonitorTypes.map((monitorType) => ({
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
          aria-label="Filter by data steward"
          className="min-w-[220px]"
        />
      </Form.Item>
    </Form>
  );
};

export default MonitorListSearchForm;
