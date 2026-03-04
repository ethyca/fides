import {
  Button,
  Card,
  Col,
  Flex,
  Form,
  Icons,
  Input,
  InputNumber,
  Row,
  Space,
  Typography,
} from "fidesui";
import { useState } from "react";

import {
  useExecuteDiscoveryMonitorMutation,
  usePutDiscoveryMonitorMutation,
} from "~/features/data-discovery-and-detection/discovery-detection.slice";
import { usePatchDatastoreConnectionMutation } from "~/features/datastore-connections/datastore-connection.slice";
import {
  AccessLevel,
  ConnectionType,
  MonitorFrequency,
  TestWebsiteMonitorParams,
} from "~/types/api";

import StatusTag from "./StatusTag";
import { makeKey, randInt, RunStatus } from "./types";

const { Title } = Typography;

type FormValues = Required<
  Pick<
    TestWebsiteMonitorParams,
    | "num_cookies"
    | "num_javascript_requests"
    | "num_image_requests"
    | "num_iframe_requests"
    | "num_browser_requests"
    | "consent_granted_percentage"
    | "consent_denied_percentage"
    | "vendor_match_percentage"
  >
> & { monitor_name?: string };

const DEFAULT_PARAMS: FormValues = {
  num_cookies: 15,
  num_javascript_requests: 10,
  num_image_requests: 5,
  num_iframe_requests: 3,
  num_browser_requests: 8,
  consent_granted_percentage: 75,
  consent_denied_percentage: 10,
  vendor_match_percentage: 60,
};

const RUNNING_STEPS = ["creating-connection", "creating-monitor", "executing"];

function randomizeParams(): FormValues {
  return {
    num_cookies: randInt(5, 50),
    num_javascript_requests: randInt(5, 30),
    num_image_requests: randInt(1, 20),
    num_iframe_requests: randInt(0, 10),
    num_browser_requests: randInt(2, 20),
    consent_granted_percentage: randInt(30, 90),
    consent_denied_percentage: randInt(0, 30),
    vendor_match_percentage: randInt(20, 90),
  };
}

const TestWebsiteMonitor = () => {
  const [initialName] = useState(() => makeKey("test-website"));
  const [form] = Form.useForm<FormValues>();
  const [runStatus, setRunStatus] = useState<RunStatus>({ step: "idle" });

  const [patchConnection] = usePatchDatastoreConnectionMutation();
  const [putMonitor] = usePutDiscoveryMonitorMutation();
  const [executeMonitor] = useExecuteDiscoveryMonitorMutation();

  const isRunning = RUNNING_STEPS.includes(runStatus.step);

  const handleRun = async () => {
    const {
      monitor_name: monitorName,
      consent_granted_percentage: grantedPct,
      consent_denied_percentage: deniedPct,
      vendor_match_percentage: vendorMatchPct,
      ...rest
    } = form.getFieldsValue();
    const params = {
      ...rest,
      consent_granted_percentage: grantedPct / 100,
      consent_denied_percentage: deniedPct / 100,
      vendor_match_percentage: vendorMatchPct / 100,
    };
    const name = monitorName!;
    const key = makeKey("test-website");
    setRunStatus({ step: "creating-connection" });

    const connResult = await patchConnection({
      key,
      name: key,
      connection_type: ConnectionType.TEST_WEBSITE,
      access: AccessLevel.READ,
      secrets: { url: "https://example.com" },
    });
    if ("error" in connResult) {
      setRunStatus({
        step: "error",
        message: "Failed to create connection. Is dev mode enabled?",
      });
      return;
    }

    setRunStatus({ step: "creating-monitor" });
    const monitorResult = await putMonitor({
      name,
      key,
      connection_config_key: key,
      execution_frequency: MonitorFrequency.NOT_SCHEDULED,
      datasource_params: params,
    });
    if ("error" in monitorResult) {
      setRunStatus({ step: "error", message: "Failed to create monitor." });
      return;
    }

    setRunStatus({ step: "executing" });
    const execResult = await executeMonitor({ monitor_config_id: key });
    if ("error" in execResult) {
      setRunStatus({ step: "error", message: "Failed to execute monitor." });
      return;
    }

    setRunStatus({
      step: "done",
      executionId: (execResult.data as any)?.monitor_execution_id,
    });
  };

  return (
    <Card title="Website Monitor">
      <Form
        form={form}
        layout="vertical"
        initialValues={{ ...DEFAULT_PARAMS, monitor_name: initialName }}
        className="mb-2"
      >
        <Form.Item
          label="Name"
          name="monitor_name"
          rules={[{ required: true }]}
        >
          <Input />
        </Form.Item>
        <Title level={5}>Assets</Title>
        <Row gutter={[12, 0]} className="mt-2">
          <Col span={8}>
            <Form.Item label="Cookies" name="num_cookies">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="JS requests" name="num_javascript_requests">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Image requests" name="num_image_requests">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="IFrame requests" name="num_iframe_requests">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Browser requests" name="num_browser_requests">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </Col>
        </Row>

        <Title level={5}>Consent and vendors</Title>
        <Row gutter={[12, 0]} className="mt-2">
          <Col span={8}>
            <Form.Item label="Granted %" name="consent_granted_percentage">
              <InputNumber
                min={0}
                max={100}
                step={5}
                addonAfter="%"
                className="w-full"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Denied %" name="consent_denied_percentage">
              <InputNumber
                min={0}
                max={100}
                step={5}
                addonAfter="%"
                className="w-full"
              />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Vendor match %" name="vendor_match_percentage">
              <InputNumber
                min={0}
                max={100}
                step={5}
                addonAfter="%"
                className="w-full"
              />
            </Form.Item>
          </Col>
        </Row>
      </Form>

      <Space direction="vertical" className="w-full">
        <Flex gap="small">
          <Button
            onClick={() => form.setFieldsValue(randomizeParams())}
            icon={<Icons.Shuffle />}
            block
          >
            Randomize params
          </Button>
          <Button
            onClick={() => form.setFieldsValue({ ...DEFAULT_PARAMS })}
            icon={<Icons.Undo />}
            block
          >
            Reset to default
          </Button>
          <Button
            type="primary"
            onClick={handleRun}
            block
            loading={isRunning}
            disabled={isRunning}
          >
            Create and run
          </Button>
        </Flex>
        <StatusTag status={runStatus} />
        {runStatus.step === "done" && (
          <Button size="small" onClick={() => setRunStatus({ step: "idle" })}>
            Run Another
          </Button>
        )}
      </Space>
    </Card>
  );
};

export default TestWebsiteMonitor;
