import { Heading, Link, OrderedList, Text, UnorderedList } from "fidesui";
import { ReactNode } from "react";

export const InfoHeading = ({ text }: { text: string }) => (
  <Heading fontSize="sm" mt={4} mb={1}>
    {text}
  </Heading>
);

export const InfoText = ({ children }: { children: ReactNode }) => (
  <Text fontSize="14px" mb={4}>
    {children}
  </Text>
);

export const InfoLink = ({
  children,
  href,
}: {
  children: ReactNode;
  href: string;
}) => (
  <Link href={href} textDecoration="underline" isExternal>
    {children}
  </Link>
);

export const InfoUnorderedList = ({ children }: { children: ReactNode }) => (
  <UnorderedList fontSize="14px" mb={4}>
    {children}
  </UnorderedList>
);

export const InfoOrderedList = ({ children }: { children: ReactNode }) => (
  <OrderedList fontSize="14px" mb={4}>
    {children}
  </OrderedList>
);

export const ToggleShowMore = ({
  showingMore,
  onClick,
}: {
  showingMore: boolean;
  onClick: () => void;
}) => (
  <Text
    fontSize="14px"
    cursor="pointer"
    textDecoration="underline"
    onClick={onClick}
  >
    {showingMore ? "Show less" : "Show more"}
  </Text>
);
