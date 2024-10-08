import { Handle, Position } from "@xyflow/react";
import { AntInput, InputRef } from "fidesui";
import { useEffect, useRef } from "react";

const TaxonomyNewNodeInput = () => {
  const inputRef = useRef<InputRef>(null);

  useEffect(() => {
    setTimeout(() => {
      inputRef.current!.focus({
        cursor: "start",
      });
    }, 200);
  }, []);

  return (
    <div className=" w-[200px]">
      <AntInput ref={inputRef} />
      <Handle type="target" position={Position.Left} />
    </div>
  );
};
export default TaxonomyNewNodeInput;
