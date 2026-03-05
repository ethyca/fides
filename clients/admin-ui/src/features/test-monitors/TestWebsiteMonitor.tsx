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
  Typography,
  useMessage,
} from "fidesui";
import { useState } from "react";

import { getErrorMessage } from "~/features/common/helpers";
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
import { isErrorResult } from "~/types/errors/api";

import { generateDefaultKey, randInt } from "./utils";

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

const DEFAULT_PARAMS: Omit<FormValues, "monitor_name"> = {
  num_cookies: 15,
  num_javascript_requests: 10,
  num_image_requests: 5,
  num_iframe_requests: 3,
  num_browser_requests: 8,
  consent_granted_percentage: 75,
  consent_denied_percentage: 10,
  vendor_match_percentage: 60,
};

function randomizeParams(): Omit<FormValues, "monitor_name"> {
  const grantedPct = randInt(30, 90);
  return {
    num_cookies: randInt(5, 50),
    num_javascript_requests: randInt(5, 30),
    num_image_requests: randInt(1, 20),
    num_iframe_requests: randInt(0, 10),
    num_browser_requests: randInt(2, 20),
    consent_granted_percentage: grantedPct,
    consent_denied_percentage: randInt(0, 100 - grantedPct),
    vendor_match_percentage: randInt(20, 90),
  };
}

const TestWebsiteMonitor = () => {
  const [key] = useState(() => generateDefaultKey("test-website"));
  const [form] = Form.useForm<FormValues>();
  const [isRunning, setIsRunning] = useState(false);
  const message = useMessage();

  const [patchConnection] = usePatchDatastoreConnectionMutation();
  const [putMonitor] = usePutDiscoveryMonitorMutation();
  const [executeMonitor] = useExecuteDiscoveryMonitorMutation();

  const handleRun = async () => {
    try {
      await form.validateFields();
    } catch {
      return;
    }
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
    setIsRunning(true);

    try {
      const connResult = await patchConnection({
        key,
        name: key,
        connection_type: ConnectionType.TEST_WEBSITE,
        access: AccessLevel.READ,
        secrets: { url: "https://example.com" },
      });
      if (isErrorResult(connResult)) {
        message.error(
          getErrorMessage(
            connResult.error,
            "Failed to create connection. Is dev mode enabled?",
          ),
        );
        return;
      }

      const monitorResult = await putMonitor({
        name,
        key,
        connection_config_key: key,
        execution_frequency: MonitorFrequency.NOT_SCHEDULED,
        datasource_params: params,
      });
      if (isErrorResult(monitorResult)) {
        message.error(
          getErrorMessage(monitorResult.error, "Failed to create monitor."),
        );
        return;
      }

      const execResult = await executeMonitor({ monitor_config_id: key });
      if (isErrorResult(execResult)) {
        message.error(
          getErrorMessage(execResult.error, "Failed to execute monitor."),
        );
        return;
      }

      const executionId = execResult.data?.monitor_execution_id;
      message.success(
        `Monitor running${executionId ? ` — execution ID: ${executionId}` : ""}`,
      );
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <Card title="Website monitor">
      <Form
        form={form}
        layout="vertical"
        initialValues={{ ...DEFAULT_PARAMS, monitor_name: key }}
        className="mb-2"
      >
        <Form.Item
          label="Monitor name"
          name="monitor_name"
          rules={[{ required: true }]}
        >
          <Input />
        </Form.Item>
        <Title level={5}>Assets</Title>
        <Row gutter={12} className="mt-2">
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
        <Row gutter={12} className="mt-2">
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
    </Card>
  );
};

export default TestWebsiteMonitor;
