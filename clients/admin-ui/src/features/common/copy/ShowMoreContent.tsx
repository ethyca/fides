import { AntButton as Button, Collapse, useDisclosure } from "fidesui";
import { ReactNode } from "react";

const ShowMoreContent = ({ children }: { children: ReactNode }) => {
  const { isOpen, onToggle } = useDisclosure();
  return (
    <>
      <Collapse in={isOpen}>{children}</Collapse>
      <Button type="link" size="small" onClick={onToggle}>
        {isOpen ? "Show less" : "Show more"}
      </Button>
    </>
  );
};

export default ShowMoreContent;
