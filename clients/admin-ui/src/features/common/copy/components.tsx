import {
  Code,
  Heading,
  HeadingProps,
  Link,
  OrderedList,
  Table,
  Tag,
  Tbody,
  Td,
  Text,
  Th,
  Thead,
  Tr,
  UnorderedList,
} from "fidesui";
import { ReactNode } from "react";

export const InfoHeading = ({
  text,
  ...props
}: { text: string } & HeadingProps) => (
  <Heading fontSize="sm" mt={4} mb={1} {...props}>
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
  <OrderedList fontSize="14px" mb={4} ml={6}>
    {children}
  </OrderedList>
);

export const InfoCodeBlock = ({ children }: { children: ReactNode }) => (
  <Code display="block" whiteSpace="pre" p={4} mb={4} overflowX="scroll">
    {children}
  </Code>
);

export interface PermissionsTableItem {
  permission: string;
  description: string;
}

export const InfoPermissionsTable = ({
  data,
}: {
  data: PermissionsTableItem[];
}) => (
  <Table fontSize="14px">
    <Thead>
      <Tr>
        <Th>Permission</Th>
        <Th>Description</Th>
      </Tr>
    </Thead>
    <Tbody>
      {data.map((item) => (
        <Tr key={item.permission}>
          <Td>
            <Tag>{item.permission}</Tag>
          </Td>
          <Td>{item.description}</Td>
        </Tr>
      ))}
    </Tbody>
  </Table>
);
