import ScrollableList from "common/ScrollableList";
import {
  Button,
  Card,
  Divider,
  Flex,
  Form,
  formatIsoLocation,
  Input,
  isoStringToEntry,
  Select,
  Space,
  Switch,
  Tag,
  Typography,
  useMessage,
} from "fidesui";
import { isEqual } from "lodash";
import { useRouter } from "next/router";
import { useEffect, useMemo, useState } from "react";

import { useAppSelector } from "~/app/hooks";
import { getErrorMessage } from "~/features/common/helpers";
import { InfoTooltip } from "~/features/common/InfoTooltip";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { PRIVACY_NOTICES_ROUTE } from "~/features/common/nav/routes";
import * as routes from "~/features/common/nav/routes";
import { PRIVACY_NOTICE_REGION_RECORD } from "~/features/common/privacy-notice-regions";
import {
  selectEnabledDataUseOptions,
  useGetAllDataUsesQuery,
} from "~/features/data-use/data-use.slice";
import { PrivacyNoticeTranslationForm } from "~/features/privacy-notices/PrivacyNoticeTranslationForm";
import {
  LimitedPrivacyNoticeResponseSchema,
  NoticeTranslation,
  PrivacyNoticeCreation,
  PrivacyNoticeRegion,
  PrivacyNoticeResponseWithRegions,
} from "~/types/api";
import type { MinimalPrivacyNotice } from "~/types/api/models/MinimalPrivacyNotice";
import type { RTKErrorResult } from "~/types/errors/api";

import {
  CONSENT_MECHANISM_OPTIONS,
  defaultInitialValues,
  ENFORCEMENT_LEVEL_OPTIONS,
  transformPrivacyNoticeResponseToCreation,
} from "./form";
import { NoticeKeyField } from "./NoticeKeyField";
import {
  selectAllPrivacyNotices,
  selectPage as selectNoticePage,
  selectPageSize as selectNoticePageSize,
  useGetAllPrivacyNoticesQuery,
  usePatchPrivacyNoticesMutation,
  usePostPrivacyNoticeMutation,
} from "./privacy-notices.slice";

const { Text } = Typography;

const PrivacyNoticeLocationDisplay = ({
  regions,
  label,
  tooltip,
}: {
  regions?: PrivacyNoticeRegion[];
  label: string;
  tooltip: string;
}) => (
  <Flex vertical align="start" gap="small">
    <Flex align="start">
      {label ? <label className="mr-1 text-xs">{label}</label> : null}
      <InfoTooltip label={tooltip} />
    </Flex>
    <div className="w-full" data-testid="notice-locations">
      <Space size={[4, 6]} wrap>
        {regions?.map((region) => {
          const isoEntry = isoStringToEntry(region);

          return (
            <Tag key={region}>
              {isoEntry
                ? formatIsoLocation({ isoEntry, showFlag: true })
                : PRIVACY_NOTICE_REGION_RECORD[region]}
            </Tag>
          );
        })}
        {!regions?.length && (
          <Text italic>
            No locations assigned. Navigate to the{" "}
            <RouterLink href={routes.PRIVACY_EXPERIENCE_ROUTE}>
              experiences view
            </RouterLink>{" "}
            configure.
          </Text>
        )}
      </Space>
    </div>
  </Flex>
);

const PrivacyNoticeForm = ({
  privacyNotice: passedInPrivacyNotice,
  availableTranslations,
}: {
  privacyNotice?: PrivacyNoticeResponseWithRegions;
  availableTranslations?: NoticeTranslation[];
}) => {
  const router = useRouter();
  const message = useMessage();
  const [form] = Form.useForm<PrivacyNoticeCreation>();

  const initialValues = useMemo(
    () =>
      passedInPrivacyNotice
        ? transformPrivacyNoticeResponseToCreation(passedInPrivacyNotice)
        : defaultInitialValues,
    [passedInPrivacyNotice],
  );

  // Query for data uses
  useGetAllDataUsesQuery();
  const dataUseOptions = useAppSelector(selectEnabledDataUseOptions);

  // Query for all privacy notices
  const allPrivacyNotices: LimitedPrivacyNoticeResponseSchema[] =
    useAppSelector(selectAllPrivacyNotices);
  const noticePage = useAppSelector(selectNoticePage);
  const noticePageSize = useAppSelector(selectNoticePageSize);
  useGetAllPrivacyNoticesQuery({ page: noticePage, size: noticePageSize });

  const getPrivacyNoticeName = ({ id }: { id: string; name: string }) => {
    const notice = allPrivacyNotices.find((n) => n.id === id);
    return notice?.name ?? id;
  };

  const isChildNotice = allPrivacyNotices.some((p) =>
    p.children?.some((c) => c.id === passedInPrivacyNotice?.id),
  );

  const [patchNoticesMutationTrigger, { isLoading: isPatching }] =
    usePatchPrivacyNoticesMutation();
  const [postNoticesMutationTrigger, { isLoading: isPosting }] =
    usePostPrivacyNoticeMutation();
  const isSubmitting = isPatching || isPosting;

  const isEditing = !!passedInPrivacyNotice;

  const handleSubmit = async (values: PrivacyNoticeCreation) => {
    try {
      if (isEditing) {
        const valuesToSubmit = {
          ...values,
          id: passedInPrivacyNotice!.id,
          translations: values.translations ?? [],
          children: values.children ?? [],
        };
        await patchNoticesMutationTrigger(valuesToSubmit).unwrap();
      } else {
        await postNoticesMutationTrigger(values).unwrap();
      }
      message.success(`Privacy notice ${isEditing ? "updated" : "created"}`);
      if (!isEditing) {
        router.push(PRIVACY_NOTICES_ROUTE);
      }
    } catch (error: unknown) {
      message.error(getErrorMessage(error as RTKErrorResult["error"]));
    }
  };

  // Watch all registered fields (including hidden Form.Items below) to drive
  // dirty/submittable re-computation.
  const allValues = Form.useWatch([], form);
  const [submittable, setSubmittable] = useState(false);
  useEffect(() => {
    const check = async () => {
      try {
        await form.validateFields({ validateOnly: true });
        setSubmittable(true);
      } catch {
        setSubmittable(false);
      }
    };
    check();
  }, [form, allValues]);

  const isDirty = useMemo(
    () => (!allValues ? false : !isEqual(allValues, initialValues)),
    // eslint-disable-next-line react-hooks/exhaustive-deps -- allValues triggers re-eval
    [allValues, initialValues],
  );

  // Read children and translations reactively via useWatch so ScrollableList
  // and the translation form stay in sync with the hidden Form.Items below.
  const children =
    (Form.useWatch("children", form) as MinimalPrivacyNotice[] | undefined) ??
    [];

  return (
    <Form
      form={form}
      layout="vertical"
      onFinish={handleSubmit}
      initialValues={initialValues}
      key={passedInPrivacyNotice?.id ?? "create"}
      data-testid="privacy-notice-form"
    >
      {/* Register fields managed outside of Form.Item (ScrollableList, the
          translations tab form) so Form.useWatch and getFieldsValue track them
          reactively. */}
      <Form.Item name="children" hidden noStyle>
        <Input />
      </Form.Item>
      <Form.Item name="translations" hidden noStyle>
        <Input />
      </Form.Item>
      <Form.Item name="disabled" hidden noStyle>
        <Input />
      </Form.Item>
      <Form.Item name="internal_description" hidden noStyle>
        <Input />
      </Form.Item>
      <Flex vertical gap="large">
        <Flex vertical gap="middle">
          <Card title="Privacy notice details">
            <Form.Item
              name="name"
              label="Notice title"
              rules={[{ required: true, message: "Title is required" }]}
            >
              <Input data-testid="input-name" />
            </Form.Item>
            <Form.Item
              name="consent_mechanism"
              label="Consent mechanism"
              rules={[
                {
                  required: true,
                  message: "Consent mechanism is required",
                },
              ]}
            >
              <Select
                options={CONSENT_MECHANISM_OPTIONS}
                aria-label="Consent mechanism"
                data-testid="select-consent_mechanism"
              />
            </Form.Item>
            <NoticeKeyField isEditing={isEditing} />
            <Form.Item
              name="has_gpc_flag"
              label="Conforms to Global Privacy Control (GPC)"
              valuePropName="checked"
            >
              <Switch data-testid="input-has_gpc_flag" />
            </Form.Item>
            <PrivacyNoticeLocationDisplay
              regions={passedInPrivacyNotice?.configured_regions}
              label="Locations where privacy notice is shown to visitors"
              tooltip="To configure locations, change the privacy experiences where this notice is shown"
            />
            <Divider />
            {!isChildNotice && (
              <div className="mb-4">
                <ScrollableList<MinimalPrivacyNotice>
                  label="Child notices"
                  addButtonLabel="Add notice children"
                  allItems={allPrivacyNotices.map((n) => ({
                    id: n.id,
                    name: n.name,
                  }))}
                  values={children}
                  setValues={(newValue) =>
                    form.setFieldValue("children", newValue)
                  }
                  idField="id"
                  getItemLabel={getPrivacyNoticeName}
                  draggable
                  baseTestId="children"
                />
              </div>
            )}
            <Form.Item name="data_uses" label="Data use">
              <Select
                options={dataUseOptions}
                mode="multiple"
                aria-label="Data use"
                data-testid="select-data_uses"
              />
            </Form.Item>
            <Form.Item
              name="enforcement_level"
              label="Enforcement level"
              rules={[
                {
                  required: true,
                  message: "Enforcement level is required",
                },
              ]}
            >
              <Select
                options={ENFORCEMENT_LEVEL_OPTIONS}
                aria-label="Enforcement level"
                data-testid="select-enforcement_level"
              />
            </Form.Item>
          </Card>
          <PrivacyNoticeTranslationForm
            availableTranslations={availableTranslations}
            initialTranslations={initialValues.translations ?? []}
            form={form}
          />
        </Flex>
        <Flex gap="small">
          <Button
            onClick={() => {
              router.back();
            }}
          >
            Cancel
          </Button>
          <Button
            htmlType="submit"
            type="primary"
            disabled={isSubmitting || !isDirty || !submittable}
            loading={isSubmitting}
            data-testid="save-btn"
          >
            Save
          </Button>
        </Flex>
      </Flex>
    </Form>
  );
};

export { PrivacyNoticeForm };
