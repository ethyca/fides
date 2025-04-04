import { formatDistance } from "date-fns";
import {
  AntTag as Tag,
  AntTooltip as Tooltip,
  AntTypography as Typography,
  Divider,
  Drawer,
  DrawerBody,
  DrawerCloseButton,
  DrawerContent,
  DrawerHeader,
  DrawerOverlay,
  useDisclosure,
} from "fidesui";
import { Fragment } from "react";

import { formatDate } from "~/features/common/utils";
import { MonitorExecutionStatus } from "~/types/api";
import { MonitorStatusResponse } from "~/types/api/models/MonitorStatusResponse";

import styles from "./MonitorStatusCell.module.scss";

const DUMMY_IN_PROGRESS_MONITOR: MonitorStatusResponse = {
  name: "Test Monitor",
  connection_config_key: "test-connection",
  execution_records: [
    {
      id: "1",
      monitor_config_key: "test-monitor",
      status: MonitorExecutionStatus.IN_PROGRESS,
    },
  ],
  last_monitored: "2024-06-04T11:11:11+00:00",
};

const DUMMY_COMPLETED_MONITOR: MonitorStatusResponse = {
  name: "Test Monitor",
  connection_config_key: "test-connection",
  execution_records: [
    {
      id: "1",
      monitor_config_key: "test-monitor",
      status: MonitorExecutionStatus.COMPLETED,
    },
  ],
  last_monitored: "2024-06-04T11:11:11+00:00",
};

const DUMMY_ERROR_MONITOR: MonitorStatusResponse = {
  name: "Test Monitor",
  connection_config_key: "test-connection",
  execution_records: [
    {
      id: "1",
      monitor_config_key: "test-monitor",
      status: MonitorExecutionStatus.ERRORED,
      messages: ["Error message 1", "Error message 2"],
      completed: "2024-06-04T11:11:11+00:00",
    },
  ],
};

const MonitorStatusCell = ({ monitor }: { monitor: MonitorStatusResponse }) => {
  //   const monitor = DUMMY_ERROR_MONITOR;
  const executionRecord = monitor.execution_records?.[0];
  const { isOpen, onOpen, onClose } = useDisclosure();
  const lastCompletedTime = monitor.last_monitored
    ? new Date(monitor.last_monitored)
    : null;

  const formattedTime = lastCompletedTime
    ? formatDate(lastCompletedTime)
    : "N/A";

  const formattedDistance = lastCompletedTime
    ? formatDistance(lastCompletedTime, new Date(), {
        addSuffix: true,
      })
    : "N/A";

  if (!executionRecord) {
    return <Tag>N/A</Tag>;
  }
  if (executionRecord.status === MonitorExecutionStatus.IN_PROGRESS) {
    if (!lastCompletedTime) {
      return <Tag color="info">Scanning</Tag>;
    }

    return (
      <Tooltip title={`Last scan: ${formattedDistance}`}>
        <Tag color="info">Scanning</Tag>
      </Tooltip>
    );
  }
  if (executionRecord.status === MonitorExecutionStatus.COMPLETED) {
    return (
      <Tooltip title={formattedTime}>
        <Tag color="success">{formattedDistance}</Tag>
      </Tooltip>
    );
  }
  if (executionRecord.status === MonitorExecutionStatus.ERRORED) {
    return (
      <>
        {/* TODO: fix hover background color */}
        <Tag color="error" className={styles.monitorStatusTag}>
          <Typography.Text onClick={onOpen} className={styles.errorTagText}>
            Incomplete
          </Typography.Text>
        </Tag>
        <Drawer isOpen={isOpen} onClose={onClose} size="md">
          <DrawerOverlay />
          <DrawerContent>
            <DrawerHeader>Failure log</DrawerHeader>
            <DrawerCloseButton />
            <DrawerBody>
              {executionRecord.completed && (
                <Typography.Paragraph className={styles.errorResultTimestamp}>
                  {formatDate(new Date(executionRecord.completed))}
                </Typography.Paragraph>
              )}
              {executionRecord.messages?.map((message, idx) => (
                // eslint-disable-next-line react/no-array-index-key
                <Fragment key={idx}>
                  <Typography.Paragraph>{message}</Typography.Paragraph>
                  {idx < executionRecord.messages!.length - 1 && (
                    <Divider className="mb-3" />
                  )}
                </Fragment>
              ))}
            </DrawerBody>
          </DrawerContent>
        </Drawer>
      </>
    );
  }
  return <Tag>N/A</Tag>;
};

export default MonitorStatusCell;
