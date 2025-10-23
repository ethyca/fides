/* eslint-disable no-console */
import {
  AntAlert as Alert,
  AntButton as Button,
  AntCard as Card,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntDivider as Divider,
  AntFlex as Flex,
  AntInput as Input,
  AntLayout as Layout,
  AntList as List,
  AntRadio as Radio,
  AntRow as Row,
  AntSelect as Select,
  AntSpace as Space,
  AntSwitch as Switch,
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Icons,
} from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import { InfoTooltip } from "~/features/common/InfoTooltip";
import PageHeader from "~/features/common/PageHeader";
import type { ListDataItem } from "~/features/poc/mockListData";
import { MOCK_LIST_DATA } from "~/features/poc/mockListData";
import { ModalMethodsCard } from "~/features/poc/ModalMethodsCard";

const { Content } = Layout;
const { Link, Paragraph, Text, Title } = Typography;

const options: { label: string; value: string }[] = [];
for (let i = 10; i < 36; i += 1) {
  options.push({
    label: i.toString(36) + i,
    value: i.toString(36) + i,
  });
}

const AntPOC: NextPage = () => {
  // Start the list component with 2 items selected to showcase
  // different states of selection
  const [selectedListKeys, setSelectedListKeys] = useState<React.Key[]>([
    "1",
    "3",
  ]);

  return (
    <Layout>
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Ant Design Proof of Concept" />
        <Row gutter={16} className="mt-6">
          <Col span={8}>
            <Card title="Button" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Button type="primary">Primary Button</Button>
                <Button>Default Button</Button>
                <Button type="dashed">Dashed Button</Button>
                <Button type="text">Text Button</Button>
                <Button type="link">Link Button</Button>
                <Button type="primary" loading>
                  Loading Button
                </Button>
                <Button type="primary" disabled>
                  Disabled Button
                </Button>
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Switch" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Switch defaultChecked />
                <Switch size="small" defaultChecked />
                <Switch loading defaultChecked />
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Select" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  options={[
                    { value: "jack", label: "Jack" },
                    { value: "lucy", label: "Lucy" },
                    { value: "Yiminghe", label: "yiminghe" },
                    { value: "disabled", label: "Disabled", disabled: true },
                  ]}
                  aria-label="Select"
                />
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  disabled
                  options={[{ value: "lucy", label: "Lucy" }]}
                  aria-label="Select"
                />
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  loading
                  options={[{ value: "lucy", label: "Lucy" }]}
                  aria-label="Select"
                />
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  allowClear
                  options={[{ value: "lucy", label: "Lucy" }]}
                  aria-label="Select"
                />
                <Select
                  mode="multiple"
                  allowClear
                  className="w-full"
                  placeholder="Please select"
                  aria-label="Select"
                  defaultValue={["a10", "c12"]}
                  options={options}
                />
                <Select
                  mode="multiple"
                  disabled
                  className="w-full"
                  placeholder="Please select"
                  aria-label="Select"
                  defaultValue={["a10", "c12"]}
                  options={options}
                />
              </Space>
            </Card>
          </Col>
        </Row>
        <br />
        <Row gutter={16}>
          <Col span={8}>
            <Card title="Checkbox" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Checkbox>Checkbox</Checkbox>
                <Checkbox defaultChecked>Checkbox</Checkbox>
                <Checkbox disabled>Disabled</Checkbox>
                <Checkbox indeterminate>Indeterminate</Checkbox>
                <Checkbox.Group
                  options={[
                    { label: "Apple", value: "Apple" },
                    { label: "Pear", value: "Pear" },
                    { label: "Orange", value: "Orange", disabled: true },
                  ]}
                  defaultValue={["Apple"]}
                />
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Radio" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Radio>Radio</Radio>
                <Radio defaultChecked>Radio</Radio>
                <Radio disabled>Disabled</Radio>
                <Radio.Group
                  options={[
                    { label: "Apple", value: "Apple" },
                    { label: "Pear", value: "Pear" },
                    { label: "Orange", value: "Orange", disabled: true },
                  ]}
                  defaultValue="Apple"
                />
                <Radio.Group
                  options={[
                    { label: "Apple", value: "Apple" },
                    { label: "Pear", value: "Pear" },
                    { label: "Orange", value: "Orange" },
                  ]}
                  defaultValue="Apple"
                  optionType="button"
                />
                <Radio.Group
                  options={[
                    { label: "Apple", value: "Apple" },
                    { label: "Pear", value: "Pear" },
                    { label: "Orange", value: "Orange" },
                  ]}
                  defaultValue="Apple"
                  optionType="button"
                  buttonStyle="solid"
                />
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Input" variant="borderless" className="h-full">
              <Space direction="vertical" size="middle">
                <Space.Compact>
                  <Input defaultValue="26888888" aria-label="Input" />
                </Space.Compact>
                <Space.Compact>
                  <Input
                    className="w-1/5"
                    defaultValue="0571"
                    aria-label="Input"
                  />
                  <Input
                    className="w-4/5"
                    defaultValue="26888888"
                    aria-label="Input"
                  />
                </Space.Compact>
                <Space.Compact>
                  <Input.Search
                    addonBefore="https://"
                    placeholder="input search text"
                    allowClear
                    aria-label="Input"
                  />
                </Space.Compact>
                <Space.Compact className="w-full">
                  <Input
                    defaultValue="Combine input and button"
                    aria-label="Input"
                  />
                  <Button type="primary">Submit</Button>
                </Space.Compact>
                <Space.Compact>
                  <Select
                    defaultValue="Zhejiang"
                    options={options}
                    aria-label="Select"
                  />
                  <Input
                    defaultValue="Xihu District, Hangzhou"
                    aria-label="Input"
                  />
                </Space.Compact>
              </Space>
            </Card>
          </Col>
        </Row>
        <br />
        <Row gutter={16}>
          <Col span={8}>
            <Card title="Tooltip" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Tooltip title="I'm a tooltip">
                  Hover or focus this text
                </Tooltip>
                <InfoTooltip label="Tooltip will show on mouse enter or focus." />
                <Tooltip title="Focus styles don't change for naturally focusable elements like buttons">
                  <Button>Button with tooltip</Button>
                </Tooltip>
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Alert" variant="borderless" className="h-full">
              <Space direction="vertical">
                <Alert message="Success Tips" type="success" showIcon />
                <Alert message="Informational Notes" type="info" showIcon />
                <Alert message="Warning" type="warning" showIcon closable />
                <Alert message="Error" type="error" showIcon />
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Tag" variant="borderless" className="h-full">
              <Flex wrap gap="small">
                <Tag color="default">default</Tag>
                <Tag color="corinth">corinth</Tag>
                <Tag color="minos">minos</Tag>
                <Tag color="terracotta">terracotta</Tag>
                <Tag color="olive">olive</Tag>
                <Tag color="marble">marble</Tag>
                <Tag color="sandstone">sandstone</Tag>
                <Tag color="nectar">nectar</Tag>
                <Tag color="error">error</Tag>
                <Tag color="warning">warning</Tag>
                <Tag color="caution">caution</Tag>
                <Tag color="success">success</Tag>
                <Tag color="info">info</Tag>
                <Tag color="alert">alert</Tag>
                <Tag color="white">white</Tag>
                <Tag closable onClose={() => console.log("closed")}>
                  Closable Tag
                </Tag>
                <Tag onClick={() => console.log("clicked")} addable />
                <Tag onClick={() => console.log("clicked")} addable>
                  Add More
                </Tag>
                <Tag hasSparkle onClick={() => console.log("clicked")}>
                  Data Use
                  <Icons.Edit />
                </Tag>
                <Tag
                  hasSparkle
                  onClick={() => console.log("clicked")}
                  closable
                  onClose={() => console.log("closed")}
                >
                  Data Category
                </Tag>
              </Flex>
            </Card>
          </Col>
        </Row>
        <br />
        <Row gutter={16}>
          <Col span={8}>
            <Card
              title="Typography Headings"
              variant="borderless"
              className="h-full"
            >
              <Space direction="vertical">
                <Title level={1}>H1 default</Title>
                <Title level={1} headingSize={2}>
                  H1 sized as H2
                </Title>
                <Title level={1} headingSize={3}>
                  H1 sized as H3
                </Title>
                <Divider style={{ margin: 0 }} />
                <Title level={2}>H2 default</Title>
                <Title level={2} headingSize={1}>
                  H2 sized as H1
                </Title>
                <Title level={2} headingSize={3}>
                  H2 sized as H3
                </Title>
                <Divider style={{ margin: 0 }} />
                <Title level={3}>H3 default</Title>
                <Title level={3} headingSize={1}>
                  H3 sized as H1
                </Title>
                <Title level={3} headingSize={2}>
                  H3 sized as H2
                </Title>
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card
              title="Typography Paragraphs"
              variant="borderless"
              className="h-full"
            >
              <Typography>
                <Paragraph>
                  This paragraph has a bottom margin. Imperdiet ex curae laoreet
                  turpis adipiscing pulvinar erat conubia rhoncus, faucibus
                  dictum porta integer tincidunt iaculis pharetra. Dis praesent
                  egestas curae tortor primis volutpat metus ridiculus sit
                  rutrum vitae ac aenean, nisi dolor a per molestie etiam ad
                  tristique magnis fames laoreet.
                </Paragraph>
                <Paragraph>
                  This paragraph has no bottom margin. Imperdiet ex curae
                  laoreet turpis adipiscing pulvinar erat conubia rhoncus,
                  faucibus dictum porta integer tincidunt iaculis pharetra.
                </Paragraph>
                <Paragraph type="secondary">
                  This paragraph uses secondary color. laoreet turpis adipiscing
                  pulvinar erat conubia rhoncus, faucibus dictum porta integer
                  tincidunt iaculis pharetra.
                </Paragraph>
              </Typography>
            </Card>
          </Col>
          <Col span={8}>
            <Card
              title="Typography Text & Link"
              variant="borderless"
              className="h-full"
            >
              <Space direction="vertical">
                <Text>Ant Design (default)</Text>
                <Text size="sm">Ant Design (small)</Text>
                <Text size="lg">Ant Design (large)</Text>
                <Text type="secondary">Ant Design (secondary)</Text>
                <Text type="success">Ant Design (success)</Text>
                <Text type="warning">Ant Design (warning)</Text>
                <Text type="danger">Ant Design (danger)</Text>
                <Text disabled>Ant Design (disabled)</Text>
                <Text mark>Ant Design (mark)</Text>
                <Text code>Ant Design (code)</Text>
                <Text keyboard>Ant Design (keyboard)</Text>
                <Text underline>Ant Design (underline)</Text>
                <Text delete>Ant Design (delete)</Text>
                <Text strong>Ant Design (strong)</Text>
                <Text italic>Ant Design (italic)</Text>
                <Link href="https://ant.design" target="_blank">
                  Ant Design (Link)
                </Link>
              </Space>
            </Card>
          </Col>
        </Row>
        <br />
        <Row gutter={16}>
          <Col span={24}>
            <Card
              title="List with rowSelection"
              variant="borderless"
              className="h-full"
            >
              <Space direction="vertical" className="w-full">
                <Text>
                  CustomList supports rowSelection similar to Table, with
                  checkboxes in the avatar position. Selected items:{" "}
                  <Text strong>{selectedListKeys.length}</Text>
                </Text>
                <List
                  dataSource={MOCK_LIST_DATA}
                  rowSelection={{
                    selectedRowKeys: selectedListKeys,
                    onChange: (keys, rows) => {
                      console.log("Selected keys:", keys);
                      console.log("Selected rows:", rows);
                      setSelectedListKeys(keys);
                    },
                    getCheckboxProps: (item: ListDataItem) => ({
                      disabled: item.locked,
                    }),
                  }}
                  renderItem={(item: ListDataItem, index, checkbox) => (
                    <List.Item
                      actions={[
                        <Button
                          key="view"
                          type="link"
                          size="small"
                          onClick={() =>
                            console.log("View clicked for:", item.title)
                          }
                        >
                          View
                        </Button>,
                      ]}
                    >
                      <List.Item.Meta
                        title={item.title}
                        description={item.description}
                        avatar={checkbox}
                      />
                      <Tag
                        color={item.status === "completed" ? "success" : "info"}
                      >
                        {item.status}
                      </Tag>
                    </List.Item>
                  )}
                />
                {selectedListKeys.length > 0 && (
                  <Alert
                    message={`${selectedListKeys.length} item(s) selected`}
                    description={
                      <Space direction="vertical" size="small">
                        <Text>
                          You can perform bulk actions on selected items.
                        </Text>
                        <Space>
                          <Button
                            size="small"
                            onClick={() =>
                              console.log("Bulk action on:", selectedListKeys)
                            }
                          >
                            Bulk action
                          </Button>
                          <Button
                            size="small"
                            onClick={() => setSelectedListKeys([])}
                          >
                            Clear selection
                          </Button>
                        </Space>
                      </Space>
                    }
                    type="info"
                    showIcon
                  />
                )}
              </Space>
            </Card>
          </Col>
        </Row>
        <br />
        <Row gutter={16}>
          <Col span={24}>
            <ModalMethodsCard />
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default AntPOC;
