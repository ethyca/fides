import { Handle, Position } from "@xyflow/react";
import { AntInput, InputRef } from "fidesui";
import { useEffect, useRef } from "react";

import { TaxonomyTreeNodeData } from "./TaxonomyTreeNode";

const TaxonomyNewNodeInput = ({ data }: { data: TaxonomyTreeNodeData }) => {
  const inputRef = useRef<InputRef>(null);

  // Set focus to the input when mounted
  // and when the parent key changes
  useEffect(() => {
    const focusOnInput = () => {
      inputRef.current!.focus({
        cursor: "start",
      });
    };
    setTimeout(focusOnInput, 200);
  }, [data.taxonomyItem?.parent_key]);

  return (
    <div className=" w-[200px]">
      <AntInput ref={inputRef} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};
export default TaxonomyNewNodeInput;
