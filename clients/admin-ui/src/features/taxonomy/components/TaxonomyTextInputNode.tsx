import { Node, NodeProps } from "@xyflow/react";
import { AntInput, InputRef } from "fidesui";
import { useEffect, useRef, useState } from "react";

import TaxonomyTreeNodeHandle from "./TaxonomyTreeNodeHandle";

export type TextInputNodeType = Node<
  {
    onCancel: () => void;
    onSubmit: (label: string) => void;
    parentKey: string;
  },
  "textInputNode"
>;

const TaxonomyTextInputNode = ({ data }: NodeProps<TextInputNodeType>) => {
  const { onCancel, onSubmit, parentKey } = data;
  const inputRef = useRef<InputRef>(null);
  const [value, setValue] = useState("");

  // Reset state and autofocus when the node is mounted
  // or when the parent key changes (it's being added to somewhere else in the tree)
  useEffect(() => {
    setValue("");
    const focusOnInput = () => {
      inputRef.current!.focus({
        cursor: "start",
      });
    };
    setTimeout(focusOnInput, 200);
  }, [parentKey]);

  return (
    <div className=" w-[200px]">
      <AntInput
        placeholder="Type label name..."
        ref={inputRef}
        onBlur={onCancel}
        onSubmit={() => onSubmit(value)}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        onKeyUp={(e) => {
          if (e.key === "Escape") {
            onCancel();
          }
        }}
        onPressEnter={() => onSubmit(value)}
      />
      <TaxonomyTreeNodeHandle type="target" />
    </div>
  );
};
export default TaxonomyTextInputNode;
