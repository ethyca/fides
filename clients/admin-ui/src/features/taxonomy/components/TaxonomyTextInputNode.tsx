import { Node, NodeProps } from "@xyflow/react";
import { AntInput as Input, AntSpin as Spin, InputRef } from "fidesui";
import { useEffect, useRef, useState } from "react";

import useCenterScreenOnNode from "../hooks/useCenterScreenOnNode";
import styles from "./TaxonomyTextInputNode.module.scss";
import TaxonomyTreeNodeHandle from "./TaxonomyTreeNodeHandle";

export type TextInputNodeType = Node<
  {
    onCancel: () => void;
    onSubmit: (label: string) => void;
    parentKey: string;
    isLoading?: boolean;
  },
  "textInputNode"
>;

const TaxonomyTextInputNode = ({
  data,
  positionAbsoluteX,
  positionAbsoluteY,
}: NodeProps<TextInputNodeType>) => {
  const { onCancel, onSubmit, parentKey, isLoading = false } = data;
  const inputRef = useRef<InputRef>(null);
  const [value, setValue] = useState("");
  const inputWidth = 200;

  const { centerScreenOnNode } = useCenterScreenOnNode({
    positionAbsoluteX,
    positionAbsoluteY,
    nodeWidth: inputWidth,
  });

  // Reset state and autofocus / center screen around the node when it is mounted
  // or when the parent key changes (it's being added to somewhere else in the tree)
  useEffect(() => {
    setValue("");
    const focusOnInput = () =>
      inputRef.current?.focus({
        cursor: "start",
        preventScroll: true,
      });

    const centerAndFocus = async () => {
      await centerScreenOnNode();
      focusOnInput();
    };

    centerAndFocus();
  }, [parentKey, centerScreenOnNode, positionAbsoluteX, positionAbsoluteY]);

  const handleSubmit = () => {
    // Prevent submission if already loading or if value is empty
    if (isLoading || !value.trim()) {
      return;
    }
    onSubmit(value);
  };

  const handleCancel = () => {
    // Prevent cancel if already loading
    if (isLoading) {
      return;
    }
    onCancel();
  };

  return (
    <div style={{ width: inputWidth }} data-testid="taxonomy-text-input-node">
      <Input
        placeholder="Type label name..."
        ref={inputRef}
        onBlur={handleCancel}
        onSubmit={handleSubmit}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyUp={(e) => {
          if (e.key === "Escape") {
            handleCancel();
          }
        }}
        onPressEnter={handleSubmit}
        className={styles.input}
        suffix={isLoading && <Spin size="small" />}
      />
      <TaxonomyTreeNodeHandle type="target" />
    </div>
  );
};
export default TaxonomyTextInputNode;
