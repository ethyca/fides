import {
  AntAlert as Alert,
  AntButton as Button,
  AntCard as Card,
  AntCheckbox as Checkbox,
  AntCol as Col,
  AntInput as Input,
  AntLayout as Layout,
  AntRadio as Radio,
  AntRow as Row,
  AntSelect as Select,
  AntSpace as Space,
  AntSwitch as Switch,
  AntTag as Tag,
  AntTooltip as Tooltip,
} from "fidesui";
import type { NextPage } from "next";

import PageHeader from "~/features/common/PageHeader";

const { Content } = Layout;

const options: { label: string; value: string }[] = [];
for (let i = 10; i < 36; i += 1) {
  options.push({
    label: i.toString(36) + i,
    value: i.toString(36) + i,
  });
}

const AntPOC: NextPage = () => {
  return (
    <Layout>
      <Content className="overflow-auto px-10 py-6">
        <PageHeader heading="Ant Design Proof of Concept" />
        <Row gutter={16}>
          <Col span={8}>
            <Card title="Button" bordered={false} className="h-full">
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
            <Card title="Switch" bordered={false} className="h-full">
              <Space direction="vertical">
                <Switch defaultChecked />
                <Switch size="small" defaultChecked />
                <Switch loading defaultChecked />
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Select" bordered={false} className="h-full">
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
                />
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  disabled
                  options={[{ value: "lucy", label: "Lucy" }]}
                />
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  loading
                  options={[{ value: "lucy", label: "Lucy" }]}
                />
                <Select
                  defaultValue="lucy"
                  className="w-32"
                  allowClear
                  options={[{ value: "lucy", label: "Lucy" }]}
                />
                <Select
                  mode="multiple"
                  allowClear
                  className="w-full"
                  placeholder="Please select"
                  defaultValue={["a10", "c12"]}
                  options={options}
                />
                <Select
                  mode="multiple"
                  disabled
                  className="w-full"
                  placeholder="Please select"
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
            <Card title="Checkbox" bordered={false} className="h-full">
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
            <Card title="Radio" bordered={false} className="h-full">
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
            <Card title="Input" bordered={false} className="h-full">
              <Space direction="vertical" size="middle">
                <Space.Compact>
                  <Input defaultValue="26888888" />
                </Space.Compact>
                <Space.Compact>
                  <Input className="w-1/5" defaultValue="0571" />
                  <Input className="w-4/5" defaultValue="26888888" />
                </Space.Compact>
                <Space.Compact>
                  <Input.Search
                    addonBefore="https://"
                    placeholder="input search text"
                    allowClear
                  />
                </Space.Compact>
                <Space.Compact className="w-full">
                  <Input defaultValue="Combine input and button" />
                  <Button type="primary">Submit</Button>
                </Space.Compact>
                <Space.Compact>
                  <Select defaultValue="Zhejiang" options={options} />
                  <Input defaultValue="Xihu District, Hangzhou" />
                </Space.Compact>
              </Space>
            </Card>
          </Col>
        </Row>
        <br />
        <Row gutter={16}>
          <Col span={8}>
            <Card title="Tooltip" bordered={false} className="h-full">
              <Space direction="vertical">
                <Tooltip title="prompt text">
                  <span>Tooltip will show on mouse enter.</span>
                </Tooltip>
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Alert" bordered={false} className="h-full">
              <Space direction="vertical">
                <Alert message="Success Tips" type="success" showIcon />
                <Alert message="Informational Notes" type="info" showIcon />
                <Alert message="Warning" type="warning" showIcon closable />
                <Alert message="Error" type="error" showIcon />
              </Space>
            </Card>
          </Col>
          <Col span={8}>
            <Card title="Tag" bordered={false} className="h-full">
              <Space direction="vertical">
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
                <Tag color="success">success</Tag>
                <Tag color="info">info</Tag>
                <Tag color="alert">alert</Tag>
                <Tag color="transparent">transparent</Tag>
              </Space>
            </Card>
          </Col>
        </Row>
      </Content>
    </Layout>
  );
};

export default AntPOC;
