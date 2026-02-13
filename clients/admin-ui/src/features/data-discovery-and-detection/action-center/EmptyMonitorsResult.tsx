import { skipToken } from "@reduxjs/toolkit/query";
import {
  Button,
  Col,
  Empty,
  Flex,
  Image,
  Paragraph,
  Row,
  Text,
  Title,
} from "fidesui";
import NextLink from "next/link";
import { useSelector } from "react-redux";

import { selectUser } from "~/features/auth";
import { SYSTEM_ROUTE } from "~/features/common/nav/routes";
import { useGetSystemsQuery } from "~/features/system";

// Immutable array partitioning
function partition<T>(array: Array<T>, index: number): [Array<T>, Array<T>] {
  return [array.toSpliced(index, array.length), array.toSpliced(0, index)];
}

function partitionLast<T>(array: Array<T>): [Array<T>, T | null] {
  const [first, last] = partition(array, Math.max(array.length - 1, 1));

  return [first, last[0]];
}

export const EmptyMonitorsResult = () => {
  const currentUser = useSelector(selectUser);

  const { data } = useGetSystemsQuery(
    currentUser?.id
      ? {
          data_stewards: [currentUser.username],
          page: 1,
          size: 3,
        }
      : skipToken,
  );

  const additionalSystemCount = (data?.total ?? 0) - (data?.items?.length || 0);

  const [systemText, last] = partitionLast([
    ...(data?.items?.map(({ name }) => name) ?? []),
    ...(additionalSystemCount > 0 ? [`${additionalSystemCount} more.`] : []),
  ]);

  return (
    <Empty
      image={
        <Flex align="center" justify="center">
          <div className="size-20">
            <Row align="middle" justify="center">
              <Col span={8} />
              <Col span={8}>
                <Image
                  rootClassName="flex"
                  src="/images/connector-logos/bigquery.svg"
                  preview={false}
                  alt=""
                />
              </Col>
              <Col span={8} />
            </Row>
            <Row align="middle" justify="center">
              <Col span={8}>
                <Image
                  rootClassName="flex"
                  src="/images/connector-logos/okta.svg"
                  preview={false}
                  alt=""
                />
              </Col>
              <Col span={8} />
              <Col span={8}>
                <Image
                  rootClassName="flex"
                  src="/images/connector-logos/snowflake.svg"
                  preview={false}
                  alt=""
                />
              </Col>
            </Row>
            <Row align="middle" justify="center">
              <Col span={8} />
              <Col span={8}>
                <Image
                  rootClassName="flex"
                  src="/images/connector-logos/generic.svg"
                  preview={false}
                  alt=""
                />
              </Col>
              <Col span={8} />
            </Row>
          </div>
          <div className="relative">
            <Image
              rootClassName="flex"
              src="/images/service.svg"
              preview={false}
              alt=""
            />
            <div className="absolute left-0 top-0 size-full">
              <Flex className="h-full" justify="center" align="center">
                <Text>Monitors</Text>
              </Flex>
            </div>
          </div>
          <div>{Empty.PRESENTED_IMAGE_SIMPLE}</div>
        </Flex>
      }
      description={
        <>
          <Title>Nothing To Review</Title>
          <Paragraph>
            You’re a steward on systems that currently have no active monitor
            results.
            <br />
            When monitors detect changes in those systems, they’ll appear here
            automatically.
          </Paragraph>
          {systemText.length > 0 && (
            <Paragraph>
              {`You’re a steward on the following systems: ${[systemText.join(", "), ...(last ? [last] : [])].join(", and ")}`}
            </Paragraph>
          )}
        </>
      }
    >
      <NextLink href={SYSTEM_ROUTE} passHref legacyBehavior>
        <Button type="primary">View inventory</Button>
      </NextLink>
    </Empty>
  );
};
