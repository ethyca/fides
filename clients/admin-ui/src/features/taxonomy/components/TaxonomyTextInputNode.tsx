import { Handle, Node, NodeProps, Position } from "@xyflow/react";
import { AntInput, InputRef } from "fidesui";
import { useEffect, useRef, useState } from "react";

export type TextInputNodeType = Node<
  {
    onBlur: () => void;
    onSubmit: () => void;
    parentKey: string;
  },
  "textInputNode"
>;

const TaxonomyTextInputNode = ({ data }: NodeProps<TextInputNodeType>) => {
  const { onBlur, onSubmit, parentKey } = data;
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
        onBlur={onBlur}
        onSubmit={onSubmit}
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};
export default TaxonomyTextInputNode;
