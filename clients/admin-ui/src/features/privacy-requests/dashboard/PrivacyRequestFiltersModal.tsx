import dayjs from "dayjs";
import {
  AntButton as Button,
  AntDatePicker as DatePicker,
  AntForm as Form,
  AntModal as Modal,
  AntSelect as Select,
} from "fidesui";

import {
  SubjectRequestActionTypeOptions,
  SubjectRequestStatusOptions,
} from "~/features/privacy-requests/constants";
import { ActionType, PrivacyRequestStatus } from "~/types/api";

interface PrivacyRequestFiltersModalProps {
  open: boolean;
  onClose: () => void;
  modalFilters: {
    from: string;
    to: string;
    status: PrivacyRequestStatus[];
    action_type: ActionType[];
  };
  setModalFilters: (filters: {
    from: string;
    to: string;
    status: PrivacyRequestStatus[];
    action_type: ActionType[];
  }) => void;
}

interface FormValues {
  dateRange?: [dayjs.Dayjs | null, dayjs.Dayjs | null] | null;
  status?: PrivacyRequestStatus[];
  action_type?: ActionType[];
}

export const PrivacyRequestFiltersModal = ({
  open,
  onClose,
  modalFilters,
  setModalFilters,
}: PrivacyRequestFiltersModalProps) => {
  const [form] = Form.useForm<FormValues>();

  // Convert modalFilters to form initial values
  const getDateRange = (): [dayjs.Dayjs | null, dayjs.Dayjs | null] | null => {
    if (modalFilters.from && modalFilters.to) {
      return [dayjs(modalFilters.from), dayjs(modalFilters.to)];
    }
    if (modalFilters.from) {
      return [dayjs(modalFilters.from), null];
    }
    if (modalFilters.to) {
      return [null, dayjs(modalFilters.to)];
    }
    return null;
  };

  const initialValues: FormValues = {
    dateRange: getDateRange(),
    status: modalFilters.status,
    action_type: modalFilters.action_type,
  };

  const handleDone = async () => {
    const values = await form.validateFields();
    const [from, to] = values.dateRange || [null, null];

    setModalFilters({
      from: from ? from.format("YYYY-MM-DD") : "",
      to: to ? to.format("YYYY-MM-DD") : "",
      status: values.status || [],
      action_type: values.action_type || [],
    });
    onClose();
  };

  const handleClearAll = () => {
    form.setFieldsValue({
      dateRange: undefined,
      status: [],
      action_type: [],
    });

    setModalFilters({
      from: "",
      to: "",
      status: [],
      action_type: [],
    });
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      title="All filters"
      footer={[
        <Button
          key="clear"
          type="text"
          onClick={handleClearAll}
          data-testid="clear-all-filters-btn"
          aria-label="Clear all filters"
        >
          Clear all
        </Button>,
        <Button
          key="done"
          type="primary"
          onClick={handleDone}
          data-testid="done-filters-btn"
          aria-label="Apply filters"
        >
          Done
        </Button>,
      ]}
    >
      <Form form={form} layout="vertical" initialValues={initialValues}>
        <Form.Item label="Date range" name="dateRange">
          <DatePicker.RangePicker
            format="YYYY-MM-DD"
            style={{ width: "100%" }}
            data-testid="date-range-picker"
          />
        </Form.Item>

        <Form.Item label="Status" name="status">
          <Select
            mode="multiple"
            placeholder="Select status"
            options={SubjectRequestStatusOptions}
            data-testid="request-status-filter"
            aria-label="Status"
          />
        </Form.Item>

        <Form.Item label="Request type" name="action_type">
          <Select
            mode="multiple"
            placeholder="Select request type"
            options={SubjectRequestActionTypeOptions}
            data-testid="request-action-type-filter"
            aria-label="Request type"
          />
        </Form.Item>
      </Form>
    </Modal>
  );
};
