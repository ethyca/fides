import {
  AntColumnsType as ColumnsType,
  AntTag as Tag,
  AntTypography as Typography,
  SelectInline,
} from "fidesui";

import DaysLeftTag from "~/features/common/DaysLeftTag";
import { formatUser } from "~/features/common/utils";
import { SubjectRequestActionTypeMap } from "~/features/privacy-requests/constants";
import {
  ActionType,
  ManualFieldListItem,
  ManualFieldRequestType,
  ManualFieldStatus,
  ManualFieldUser,
  PrivacyRequestStatus,
} from "~/types/api";

import { ActionButtons } from "../components/ActionButtons";
import {
  REQUEST_TYPE_FILTER_OPTIONS,
  STATUS_FILTER_OPTIONS,
  STATUS_MAP,
} from "../constants";

interface FilterOption {
  text: string;
  value: string;
}

interface ManualTaskFilters {
  status?: string;
  systemName?: string;
  requestType?: string;
  assignedUsers?: string;
  privacyRequestId?: string;
}

interface UserOption {
  label: string;
  value: string;
}

interface UseManualTaskColumnsProps {
  systemFilters: FilterOption[];
  userFilters: FilterOption[];
  onUserClick: (userId: string) => void;
  currentFilters: ManualTaskFilters;
  hasAccessToAllTasks: boolean;
}

export const useManualTaskColumns = ({
  systemFilters,
  userFilters,
  onUserClick,
  currentFilters,
  hasAccessToAllTasks,
}: UseManualTaskColumnsProps): ColumnsType<ManualFieldListItem> => {
  const allColumns: ColumnsType<ManualFieldListItem> = [
    {
      title: "Task name",
      dataIndex: "name",
      key: "name",
      width: 300,
      render: (name) => (
        <Typography.Text
          ellipsis={{ tooltip: name }}
          className="!max-w-[300px]"
        >
          {name}
        </Typography.Text>
      ),
    },
    {
      title: "Status",
      dataIndex: "status",
      key: "status",
      width: 120,
      render: (status: ManualFieldStatus) => (
        <Tag
          color={STATUS_MAP[status].color}
          data-testid="manual-task-status-tag"
        >
          {STATUS_MAP[status].label}
        </Tag>
      ),
      filters: STATUS_FILTER_OPTIONS,
      filterMultiple: false,
    },
    {
      title: "System",
      dataIndex: ["system", "name"],
      key: "system_name",
      width: 210,
      render: (systemName: string) => (
        <Typography.Text
          ellipsis={{ tooltip: systemName }}
          className="!max-w-[210px]"
        >
          {systemName}
        </Typography.Text>
      ),
      filters: systemFilters,
      filterMultiple: false,
    },
    {
      title: "Type",
      dataIndex: "request_type",
      key: "request_type",
      width: 150,
      render: (type: ManualFieldRequestType) => {
        const actionType =
          type === ManualFieldRequestType.ACCESS
            ? ActionType.ACCESS
            : ActionType.ERASURE;
        const displayName = SubjectRequestActionTypeMap.get(actionType) || type;
        return <Typography.Text>{displayName}</Typography.Text>;
      },
      filters: REQUEST_TYPE_FILTER_OPTIONS,
      filterMultiple: false,
    },
    {
      title: "Assigned to",
      dataIndex: "assigned_users",
      key: "assigned_users",
      width: 380,
      render: (assignedUsers: ManualFieldUser[]) => {
        if (!assignedUsers || assignedUsers.length === 0) {
          return <Typography.Text>-</Typography.Text>;
        }

        const userOptions: UserOption[] = assignedUsers.map((user) => ({
          label: formatUser(user),
          value: user.id,
        }));

        const currentAssignedUserIds = assignedUsers.map((user) => user.id);

        return (
          <SelectInline
            value={currentAssignedUserIds}
            options={userOptions}
            readonly
            onTagClick={(userId) => onUserClick(String(userId))}
          />
        );
      },
      filters: userFilters,
      filterMultiple: false,
      defaultFilteredValue: currentFilters.assignedUsers
        ? [currentFilters.assignedUsers]
        : undefined,
    },
    {
      title: "Days left",
      dataIndex: ["privacy_request", "days_left"],
      key: "days_left",
      width: 140,
      render: (daysLeft: number | null) => (
        <DaysLeftTag
          daysLeft={daysLeft || 0}
          includeText={false}
          status={PrivacyRequestStatus.PENDING}
        />
      ),
    },
    {
      title: "Subject identity",
      dataIndex: ["privacy_request", "subject_identities"],
      key: "subject_identities",
      width: 200,
      render: (subjectIdentities: Record<string, string>) => {
        if (!subjectIdentities) {
          return <Typography.Text>-</Typography.Text>;
        }

        // Display email or phone_number if available
        const identity =
          subjectIdentities.email || subjectIdentities.phone_number || "";
        return (
          <Typography.Text ellipsis={{ tooltip: identity }}>
            {identity}
          </Typography.Text>
        );
      },
    },
    {
      title: "Actions",
      key: "actions",
      width: 120,
      render: (_, record) => <ActionButtons task={record} />,
    },
  ];

  // If user doesn't have access to all tasks, remove the "Assigned to" column
  if (!hasAccessToAllTasks) {
    return allColumns.filter((column) => column.key !== "assigned_users");
  }

  return allColumns;
};
