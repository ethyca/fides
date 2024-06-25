import { Collapse, Text, useDisclosure } from "fidesui";
import { ReactNode } from "react";

const ShowMoreContent = ({ children }: { children: ReactNode }) => {
  const { isOpen, onToggle } = useDisclosure();
  return (
    <>
      <Collapse in={isOpen}>{children}</Collapse>
      <Text
        fontSize="sm"
        cursor="pointer"
        textDecoration="underline"
        onClick={onToggle}
      >
        {isOpen ? "Show less" : "Show more"}
      </Text>
    </>
  );
};

export default ShowMoreContent;
