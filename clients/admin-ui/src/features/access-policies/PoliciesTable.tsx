import type { Identifier, XYCoord } from "dnd-core";
import { Button, Dropdown, Icons, Switch, Table, Tag, Text } from "fidesui";
import NextLink from "next/link";
import React, { useCallback, useRef } from "react";
import { useDrag, useDrop } from "react-dnd";

import { ControlGroup } from "./access-policies.slice";
import { AccessPolicyListItem } from "./types";

const ROW_TYPE = "PolicyTableRow";

interface DragItem {
  index: number;
  id: string;
  type: string;
}

interface DraggableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  index: number;
  moveRow: (dragIndex: number, hoverIndex: number) => void;
  "data-row-key"?: string;
}

const DraggableRow = ({
  index,
  moveRow,
  className,
  style,
  children,
  ...restProps
}: DraggableRowProps) => {
  const ref = useRef<HTMLTableRowElement>(null);
  const rowKey = restProps["data-row-key"] ?? "";

  const [{ handlerId }, drop] = useDrop<
    DragItem,
    void,
    { handlerId: Identifier | null }
  >({
    accept: ROW_TYPE,
    collect(monitor) {
      return { handlerId: monitor.getHandlerId() };
    },
    hover(item: DragItem, monitor) {
      if (!ref.current) {
        return;
      }
      const dragIndex = item.index;
      const hoverIndex = index;
      if (dragIndex === hoverIndex) {
        return;
      }

      const hoverBoundingRect = ref.current.getBoundingClientRect();
      const hoverMiddleY =
        (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;
      const clientOffset = monitor.getClientOffset();
      const hoverClientY = (clientOffset as XYCoord).y - hoverBoundingRect.top;

      if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY) {
        return;
      }
      if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY) {
        return;
      }

      moveRow(dragIndex, hoverIndex);
      Object.assign(item, { index: hoverIndex });
    },
  });

  const [{ isDragging }, drag] = useDrag({
    type: ROW_TYPE,
    item: () => ({ id: rowKey, index }),
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
  });

  // Make the row both the drag source and drop target (same pattern as DraggableColumnList)
  drag(drop(ref));

  return (
    <tr
      ref={ref}
      className={className}
      style={{ ...style, opacity: isDragging ? 0.4 : 1, cursor: "grab" }}
      data-handler-id={handlerId}
      {...restProps}
    >
      {children}
    </tr>
  );
};

const formatRelativeTime = (isoDate?: string): string => {
  if (!isoDate) {
    return "—";
  }
  const diff = Date.now() - new Date(isoDate).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) {
    return "Just now";
  }
  if (minutes < 60) {
    return `${minutes}m ago`;
  }
  const hours = Math.floor(minutes / 60);
  if (hours < 24) {
    return `${hours}h ago`;
  }
  const days = Math.floor(hours / 24);
  return `${days}d ago`;
};

const DragHandle = () => (
  <Icons.Draggable size={16} style={{ color: "var(--fidesui-neutral-500)" }} />
);

interface PoliciesTableProps {
  policies: AccessPolicyListItem[];
  controlGroups: ControlGroup[];
  onToggle: (policy: AccessPolicyListItem) => void;
  onReorder: (
    policies: AccessPolicyListItem[],
    fromIndex: number,
    toIndex: number,
  ) => void;
  onEdit: (policy: AccessPolicyListItem) => void;
  onDuplicate: (policy: AccessPolicyListItem) => void;
  onDelete: (policy: AccessPolicyListItem) => void;
  isLoading: boolean;
}

const PoliciesTable = ({
  policies,
  controlGroups,
  onToggle,
  onReorder,
  onEdit,
  onDuplicate,
  onDelete,
  isLoading,
}: PoliciesTableProps) => {
  const controlGroupMap = new Map(
    controlGroups.map((cg) => [cg.key, cg.label]),
  );

  const moveRow = useCallback(
    (dragIndex: number, hoverIndex: number) => {
      onReorder(policies, dragIndex, hoverIndex);
    },
    [policies, onReorder],
  );

  const columns = [
    {
      title: "",
      dataIndex: "drag",
      key: "drag",
      width: 40,
      render: () => <DragHandle />,
    },
    {
      title: "#",
      dataIndex: "priority",
      key: "priority",
      width: 60,
      render: (_: unknown, record: AccessPolicyListItem) => (
        <Text size="sm" type="secondary">
          {record.priority}
        </Text>
      ),
    },
    {
      title: "Name",
      dataIndex: "name",
      key: "name",
      ellipsis: true,
      render: (_: unknown, record: AccessPolicyListItem) => (
        <NextLink href={`/access-policies/edit/${record.id}`}>
          <Text strong>{record.name}</Text>
        </NextLink>
      ),
    },
    {
      title: "Description",
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      render: (text: string) => (
        <Text size="sm" type="secondary">
          {text}
        </Text>
      ),
    },
    {
      title: "Controls",
      dataIndex: "controls",
      key: "controls",
      width: 200,
      render: (_: unknown, record: AccessPolicyListItem) =>
        record.controls?.map((key) => (
          <Tag key={key} className="mb-1">
            {controlGroupMap.get(key) ?? key}
          </Tag>
        )),
    },
    {
      title: "Decision",
      dataIndex: "decision",
      key: "decision",
      width: 100,
      render: (_: unknown, record: AccessPolicyListItem) =>
        record.decision ? (
          <Tag color={record.decision === "ALLOW" ? "success" : "error"}>
            {record.decision}
          </Tag>
        ) : null,
    },
    {
      title: "Enabled",
      dataIndex: "enabled",
      key: "enabled",
      width: 80,
      render: (_: unknown, record: AccessPolicyListItem) => (
        <Switch
          size="small"
          checked={record.enabled}
          onChange={() => onToggle(record)}
        />
      ),
    },
    {
      title: "Updated",
      dataIndex: "updated_at",
      key: "updated_at",
      width: 100,
      render: (text: string) => (
        <Text size="sm" type="secondary">
          {formatRelativeTime(text)}
        </Text>
      ),
    },
    {
      title: "",
      key: "actions",
      width: 48,
      render: (_: unknown, record: AccessPolicyListItem) => (
        <Dropdown
          menu={{
            items: [
              {
                key: "edit",
                label: "Edit",
                onClick: () => onEdit(record),
              },
              {
                key: "duplicate",
                label: "Duplicate",
                onClick: () => onDuplicate(record),
              },
              {
                key: "delete",
                label: "Delete",
                danger: true,
                onClick: () => onDelete(record),
              },
            ],
          }}
          trigger={["click"]}
        >
          <Button
            aria-label="Policy actions"
            type="text"
            size="small"
            icon={<Icons.OverflowMenuVertical />}
          />
        </Dropdown>
      ),
    },
  ];

  return (
    <Table
      dataSource={policies}
      columns={columns}
      rowKey="id"
      loading={isLoading}
      pagination={false}
      components={{
        body: {
          row: DraggableRow,
        },
      }}
      onRow={(_, index) =>
        ({
          index,
          moveRow,
        }) as React.HTMLAttributes<HTMLTableRowElement>
      }
    />
  );
};

export default PoliciesTable;
