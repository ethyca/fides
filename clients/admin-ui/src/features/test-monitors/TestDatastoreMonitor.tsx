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
  TestMonitorParams,
} from "~/types/api";

import StatusTag from "./StatusTag";
import { makeKey, randInt, RunStatus } from "./types";

type FormValues = Required<
  Pick<
    TestMonitorParams,
    | "num_databases"
    | "num_schemas_per_db"
    | "num_tables_per_schema"
    | "num_fields_per_table"
    | "max_nesting_level"
    | "nested_field_percentage"
  >
> & { monitor_name?: string };

const DEFAULT_PARAMS: FormValues = {
  num_databases: 2,
  num_schemas_per_db: 2,
  num_tables_per_schema: 2,
  num_fields_per_table: 10,
  max_nesting_level: 2,
  nested_field_percentage: 20,
};

const RUNNING_STEPS = ["creating-connection", "creating-monitor", "executing"];

function randomizeParams(): FormValues {
  return {
    num_databases: randInt(1, 10),
    num_schemas_per_db: randInt(1, 5),
    num_tables_per_schema: randInt(1, 10),
    num_fields_per_table: randInt(5, 50),
    max_nesting_level: randInt(0, 4),
    nested_field_percentage: randInt(0, 50),
  };
}

const TestDatastoreMonitor = () => {
  const [initialName] = useState(() => makeKey("test-datastore"));
  const [form] = Form.useForm<FormValues>();
  const [runStatus, setRunStatus] = useState<RunStatus>({ step: "idle" });

  const [patchConnection] = usePatchDatastoreConnectionMutation();
  const [putMonitor] = usePutDiscoveryMonitorMutation();
  const [executeMonitor] = useExecuteDiscoveryMonitorMutation();

  const isRunning = RUNNING_STEPS.includes(runStatus.step);

  const handleRun = async () => {
    const {
      monitor_name: monitorName,
      nested_field_percentage: nestedFieldPct,
      ...rest
    } = form.getFieldsValue();
    const params = {
      ...rest,
      nested_field_percentage: nestedFieldPct / 100,
    };
    const name = monitorName!;
    const key = makeKey("test-datastore");
    setRunStatus({ step: "creating-connection" });

    const connResult = await patchConnection({
      key,
      name: key,
      connection_type: ConnectionType.TEST_DATASTORE,
      access: AccessLevel.WRITE,
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
    <Card title="Datastore monitor">
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
        <Row gutter={[12, 0]}>
          <Col span={8}>
            <Form.Item label="Databases" name="num_databases">
              <InputNumber min={1} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Schemas / DB" name="num_schemas_per_db">
              <InputNumber min={1} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Tables / Schema" name="num_tables_per_schema">
              <InputNumber min={1} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Fields / Table" name="num_fields_per_table">
              <InputNumber min={1} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Max nesting level" name="max_nesting_level">
              <InputNumber min={0} className="w-full" />
            </Form.Item>
          </Col>
          <Col span={8}>
            <Form.Item label="Nested field %" name="nested_field_percentage">
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

      <Space className="w-full" direction="vertical">
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
            loading={isRunning}
            disabled={isRunning}
            block
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

export default TestDatastoreMonitor;
