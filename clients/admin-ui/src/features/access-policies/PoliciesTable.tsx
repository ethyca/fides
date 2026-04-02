import classNames from "classnames";
import type { Identifier, XYCoord } from "dnd-core";
import { Flex, Icons, Input, Switch, Table, Tag, Text } from "fidesui";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { DndProvider, useDrag, useDrop } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";

import { InfoTooltip } from "~/features/common/InfoTooltip";
import { ACCESS_POLICY_EDIT_ROUTE } from "~/features/common/nav/routes";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { TagExpandableCell } from "~/features/common/table/cells/TagExpandableCell";

import { ControlGroup } from "./access-policies.slice";
import { DECISION_LABELS } from "./constants";
import styles from "./PoliciesTable.module.scss";
import { AccessPolicyListItem, ActionType } from "./types";
import { formatRelativeTime } from "./utils";

const ROW_TYPE = "PolicyTableRow";

interface DragItem {
  index: number;
  originalIndex: number;
  id: string;
  type: string;
}

interface DraggableRowProps extends React.HTMLAttributes<HTMLTableRowElement> {
  index: number;
  moveRow: (dragIndex: number, hoverIndex: number) => void;
  onRowDragEnd: (
    originalIndex: number,
    finalIndex: number,
    dropped: boolean,
  ) => void;
  "data-row-key"?: string;
}

const DraggableRow = ({
  index,
  moveRow,
  onRowDragEnd,
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
      // eslint-disable-next-line no-param-reassign
      item.index = hoverIndex;
    },
  });

  const [{ isDragging }, drag] = useDrag({
    type: ROW_TYPE,
    item: () => ({ id: rowKey, index, originalIndex: index }),
    collect: (monitor) => ({
      isDragging: !!monitor.isDragging(),
    }),
    end: (item, monitor) => {
      onRowDragEnd(item.originalIndex, item.index, monitor.didDrop());
    },
  });

  drag(drop(ref));

  return (
    <tr
      ref={ref}
      className={classNames(className, styles.draggableRow, {
        [styles.isDragging]: isDragging,
      })}
      style={style}
      data-handler-id={handlerId}
      {...restProps}
    >
      {children}
    </tr>
  );
};

const DragHandle = () => (
  <Icons.Draggable size={16} color="var(--fidesui-neutral-500)" />
);

interface EditablePriorityCellProps {
  value: number;
  onEdit: (newValue: number) => void;
}

const EditablePriorityCell = ({ value, onEdit }: EditablePriorityCellProps) => {
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState(String(value));
  const [isHovered, setIsHovered] = useState(false);

  const commit = () => {
    const parsed = parseInt(inputValue, 10);
    if (!Number.isNaN(parsed) && parsed !== value) {
      onEdit(parsed);
    }
    setIsEditing(false);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      commit();
    } else if (e.key === "Escape") {
      setInputValue(String(value));
      setIsEditing(false);
    }
  };

  if (isEditing) {
    return (
      <Input
        autoFocus
        size="small"
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onBlur={commit}
        onKeyDown={handleKeyDown}
        style={{ width: 56 }}
        type="number"
      />
    );
  }

  return (
    <Flex
      align="center"
      gap="small"
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={styles.priorityCellWrapper}
    >
      <Text size="sm" type="secondary">
        {value}
      </Text>
      <button
        type="button"
        aria-label="Edit priority"
        onClick={() => {
          setInputValue(String(value));
          setIsEditing(true);
        }}
        className={classNames(styles.editButton, {
          [styles.visible]: isHovered,
        })}
      >
        <Icons.Edit size={12} color="var(--fidesui-neutral-500)" />
      </button>
    </Flex>
  );
};

interface PoliciesTableProps {
  policies: AccessPolicyListItem[];
  controlGroups: ControlGroup[];
  onToggle: (policy: AccessPolicyListItem) => void;
  onReorder: (
    policies: AccessPolicyListItem[],
    fromIndex: number,
    toIndex: number,
  ) => void;
  onPriorityEdit: (policy: AccessPolicyListItem, newPriority: number) => void;
  isLoading: boolean;
}

const PoliciesTable = ({
  policies,
  controlGroups,
  onToggle,
  onReorder,
  onPriorityEdit,
  isLoading,
}: PoliciesTableProps) => {
  const controlGroupMap = useMemo(
    () => new Map(controlGroups.map((cg) => [cg.key, cg.label])),
    [controlGroups],
  );

  // Local state drives the visible order during drag; only synced from props
  // when not dragging so in-flight visual reorders aren't overwritten.
  const [localPolicies, setLocalPolicies] = useState(policies);
  const isDraggingRef = useRef(false);

  useEffect(() => {
    if (!isDraggingRef.current) {
      setLocalPolicies(policies);
    }
  }, [policies]);

  // Called on every hover crossing — updates visual order only, no API calls.
  const moveRow = useCallback((dragIndex: number, hoverIndex: number) => {
    isDraggingRef.current = true;
    setLocalPolicies((prev) => {
      const next = [...prev];
      const [moved] = next.splice(dragIndex, 1);
      next.splice(hoverIndex, 0, moved);
      return next;
    });
  }, []);

  // Called once when drag ends — fires the API only if position actually changed.
  const handleDragEnd = useCallback(
    (originalIndex: number, finalIndex: number, dropped: boolean) => {
      isDraggingRef.current = false;
      if (!dropped || originalIndex === finalIndex) {
        // Drag was cancelled or dropped in the same spot — reset visual state.
        setLocalPolicies(policies);
        return;
      }
      onReorder(policies, originalIndex, finalIndex);
    },
    [policies, onReorder],
  );

  const columns = useMemo(
    () => [
      {
        title: "",
        dataIndex: "drag",
        key: "drag",
        width: 50,
        render: () => <DragHandle />,
      },
      {
        title: (
          <Flex align="center" gap="small">
            #
            <InfoTooltip label="Priority — policies are evaluated in this order" />
          </Flex>
        ),
        dataIndex: "priority",
        key: "priority",
        width: 90,
        render: (_: unknown, record: AccessPolicyListItem) => (
          <EditablePriorityCell
            value={record.priority}
            onEdit={(newPriority) => onPriorityEdit(record, newPriority)}
          />
        ),
      },
      {
        title: "Name",
        dataIndex: "name",
        key: "name",
        width: 220,
        ellipsis: true,
        render: (_: unknown, record: AccessPolicyListItem) => (
          <LinkCell
            href={{
              pathname: ACCESS_POLICY_EDIT_ROUTE,
              query: { id: record.id },
            }}
          >
            {record.name}
          </LinkCell>
        ),
      },
      {
        title: "Description",
        dataIndex: "description",
        key: "description",
        minWidth: 160,
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
        width: 240,
        render: (_: unknown, record: AccessPolicyListItem) => (
          <TagExpandableCell
            values={record.controls?.map((key) => ({
              key,
              label: controlGroupMap.get(key) ?? key,
            }))}
          />
        ),
      },
      {
        title: "Decision",
        dataIndex: "decision",
        key: "decision",
        width: 100,
        render: (_: unknown, record: AccessPolicyListItem) =>
          record.decision ? (
            <Tag
              color={record.decision === ActionType.ALLOW ? "success" : "error"}
            >
              {DECISION_LABELS[record.decision] ?? record.decision}
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
        width: 90,
        render: (text: string) => (
          <Text size="sm" type="secondary">
            {formatRelativeTime(text)}
          </Text>
        ),
      },
    ],
    [controlGroupMap, onToggle, onPriorityEdit],
  );

  return (
    <DndProvider backend={HTML5Backend}>
      <Table
        dataSource={localPolicies}
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
            onRowDragEnd: handleDragEnd,
          }) as unknown as React.HTMLAttributes<HTMLTableRowElement>
        }
        tableLayout="fixed"
        scroll={{ scrollToFirstRowOnChange: true }}
      />
    </DndProvider>
  );
};

export default PoliciesTable;
