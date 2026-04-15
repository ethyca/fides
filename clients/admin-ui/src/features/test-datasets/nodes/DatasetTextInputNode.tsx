import { Node, NodeProps, useReactFlow } from "@xyflow/react";
import { Input, InputRef } from "fidesui";
import { useEffect, useRef, useState } from "react";

import styles from "./DatasetNode.module.scss";
import DatasetNodeHandle from "./DatasetNodeHandle";

export type DatasetTextInputNodeData = {
  parentId: string;
  mode: "collection" | "field";
  existingNames: string[];
  onCancel: () => void;
  onSubmit: (name: string) => void;
  [key: string]: unknown;
};

export type DatasetTextInputNodeType = Node<
  DatasetTextInputNodeData,
  "datasetTextInputNode"
>;

const NAME_PATTERN = /^[a-zA-Z0-9_]+$/;
const INPUT_WIDTH = 220;

const validateName = (
  value: string,
  existingNames: string[],
): string | null => {
  const trimmed = value.trim();
  if (!trimmed) {
    return "Name is required";
  }
  if (!NAME_PATTERN.test(trimmed)) {
    return "Only letters, numbers, and underscores";
  }
  if (existingNames.includes(trimmed)) {
    return "A node with this name already exists";
  }
  return null;
};

const DatasetTextInputNode = ({
  data,
  positionAbsoluteX,
  positionAbsoluteY,
}: NodeProps<DatasetTextInputNodeType>) => {
  const { parentId, mode, existingNames, onCancel, onSubmit } = data;
  const inputRef = useRef<InputRef>(null);
  const [value, setValue] = useState("");
  const [error, setError] = useState<string | null>(null);
  const { setCenter, getZoom } = useReactFlow();

  // Center on the draft node and focus the input. Re-runs when the parent
  // changes (user clicks + on a different node without canceling first).
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      await setCenter(positionAbsoluteX + INPUT_WIDTH / 2, positionAbsoluteY, {
        duration: 400,
        zoom: getZoom(),
      });
      if (!cancelled) {
        inputRef.current?.focus({ cursor: "start", preventScroll: true });
      }
    };
    run();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [parentId]);

  const handleSubmit = () => {
    const validation = validateName(value, existingNames);
    if (validation) {
      setError(validation);
      return;
    }
    onSubmit(value.trim());
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setValue(e.target.value);
    if (error) {
      setError(null);
    }
  };

  return (
    <div
      style={{ width: INPUT_WIDTH, position: "relative" }}
      data-testid="dataset-text-input-node"
    >
      <DatasetNodeHandle type="target" />
      <Input
        ref={inputRef}
        className={styles.input}
        placeholder={mode === "collection" ? "Collection name…" : "Field name…"}
        value={value}
        status={error ? "error" : undefined}
        onChange={handleChange}
        onBlur={onCancel}
        onKeyUp={(e) => {
          if (e.key === "Escape") {
            onCancel();
          }
        }}
        onPressEnter={handleSubmit}
        size="small"
      />
      {error && (
        <div
          style={{
            position: "absolute",
            top: "100%",
            left: 0,
            marginTop: 4,
            fontSize: 11,
            color: "var(--fidesui-error)",
            whiteSpace: "nowrap",
          }}
        >
          {error}
        </div>
      )}
    </div>
  );
};

export default DatasetTextInputNode;
