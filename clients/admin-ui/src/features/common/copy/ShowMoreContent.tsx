import { AntCollapse as Collapse, useDisclosure } from "fidesui";
import { ReactNode } from "react";

const ShowMoreContent = ({ children }: { children: ReactNode }) => {
  const { isOpen, onToggle } = useDisclosure();
  return (
    <Collapse
      ghost
      size="small"
      activeKey={isOpen ? ["1"] : []}
      onChange={(keys) => {
        const shouldBeOpen = keys.includes("1");
        if (shouldBeOpen !== isOpen) {
          onToggle();
        }
      }}
      items={[
        {
          key: "1",
          label: isOpen ? "Show less" : "Show more",
          children,
        },
      ]}
    />
  );
};

export default ShowMoreContent;
