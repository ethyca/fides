import {
  closestCenter,
  DndContext,
  DragEndEvent,
  DragOverEvent,
  DragStartEvent,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import classNames from "classnames";
import { Flex, Icons, Input, Switch, Table, Text } from "fidesui";
import React, {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";
import { ACCESS_POLICY_EDIT_ROUTE } from "~/features/common/nav/routes";
import { LinkCell } from "~/features/common/table/cells/LinkCell";
import { TagExpandableCell } from "~/features/common/table/cells/TagExpandableCell";

import { Control } from "./access-policies.slice";
import DecisionTag from "./DecisionTag";
import styles from "./PoliciesTable.module.scss";
import { AccessPolicyListItem } from "./types";
import { formatRelativeTime } from "./utils";

type SortableRowProps = React.HTMLAttributes<HTMLTableRowElement> & {
  "data-row-key"?: string;
};

const SortableRow = ({
  className,
  style,
  children,
  ...restProps
}: SortableRowProps) => {
  const rowKey = restProps["data-row-key"] ?? "";
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: rowKey });

  const rowStyle: React.CSSProperties = {
    ...style,
    transform: CSS.Transform.toString(transform),
    transition,
  };

  return (
    <tr
      ref={setNodeRef}
      className={classNames(className, styles.draggableRow, {
        [styles.isDragging]: isDragging,
      })}
      style={rowStyle}
      {...attributes}
      {...listeners}
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
  controlGroups: Control[];
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
  const originalIndexRef = useRef<number | null>(null);

  useEffect(() => {
    if (!isDraggingRef.current) {
      setLocalPolicies(policies);
    }
  }, [policies]);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  );

  const items = useMemo(() => localPolicies.map((p) => p.id), [localPolicies]);

  const handleDragStart = useCallback(
    (event: DragStartEvent) => {
      isDraggingRef.current = true;
      originalIndexRef.current = localPolicies.findIndex(
        (p) => p.id === event.active.id,
      );
    },
    [localPolicies],
  );

  // Updates visual order on every hover crossing, no API calls.
  const handleDragOver = useCallback((event: DragOverEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) {
      return;
    }
    setLocalPolicies((prev) => {
      const oldIndex = prev.findIndex((p) => p.id === active.id);
      const newIndex = prev.findIndex((p) => p.id === over.id);
      if (oldIndex === -1 || newIndex === -1 || oldIndex === newIndex) {
        return prev;
      }
      return arrayMove(prev, oldIndex, newIndex);
    });
  }, []);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      isDraggingRef.current = false;
      const originalIndex = originalIndexRef.current;
      originalIndexRef.current = null;
      const { active, over } = event;

      if (!over || originalIndex === null) {
        setLocalPolicies(policies);
        return;
      }

      const finalIndex = localPolicies.findIndex((p) => p.id === active.id);
      if (finalIndex === -1 || finalIndex === originalIndex) {
        setLocalPolicies(policies);
        return;
      }

      onReorder(policies, originalIndex, finalIndex);
    },
    [policies, localPolicies, onReorder],
  );

  const handleDragCancel = useCallback(() => {
    isDraggingRef.current = false;
    originalIndexRef.current = null;
    setLocalPolicies(policies);
  }, [policies]);

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
        title: "Control",
        dataIndex: "control",
        key: "control",
        width: 240,
        render: (_: unknown, record: AccessPolicyListItem) => (
          <TagExpandableCell
            values={
              record.control
                ? [
                    {
                      key: record.control,
                      label:
                        controlGroupMap.get(record.control) ?? record.control,
                    },
                  ]
                : undefined
            }
          />
        ),
      },
      {
        title: "Decision",
        dataIndex: "decision",
        key: "decision",
        width: 100,
        render: (_: unknown, record: AccessPolicyListItem) =>
          record.decision ? <DecisionTag decision={record.decision} /> : null,
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
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={handleDragEnd}
      onDragCancel={handleDragCancel}
    >
      <SortableContext items={items} strategy={verticalListSortingStrategy}>
        <Table
          dataSource={localPolicies}
          columns={columns}
          rowKey="id"
          loading={isLoading}
          pagination={false}
          components={{
            body: {
              row: SortableRow,
            },
          }}
          tableLayout="fixed"
          scroll={{ scrollToFirstRowOnChange: true }}
        />
      </SortableContext>
    </DndContext>
  );
};

export default PoliciesTable;
