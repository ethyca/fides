import {
  Button,
  Flex,
  Input,
  Result,
  Select,
  Space,
  Typography,
} from "fidesui";
import palette from "fidesui/src/palette/palette.module.scss";
import type { NextPage } from "next";
import { useRouter } from "next/router";
import { useState } from "react";

import { useFeatures } from "~/features/common/features";
import Layout from "~/features/common/Layout";
import { PRIVACY_ASSESSMENTS_ROUTE } from "~/features/common/nav/routes";
import PageHeader from "~/features/common/PageHeader";

import { dpoOptions, frameworks, mockSystemNames } from "./constants";

const { Text } = Typography;

const NewAssessmentPage: NextPage = () => {
  const { flags } = useFeatures();
  const router = useRouter();

  const defaultFramework =
    typeof router.query.framework === "string"
      ? router.query.framework
      : "gdpr";

  const [form, setForm] = useState({
    name: "",
    framework: defaultFramework,
    dpo: "",
    description: "",
    systemName: "",
  });

  if (!flags?.alphaDataProtectionAssessments) {
    return (
      <Layout title="New assessment">
        <Result
          status="error"
          title="Feature not available"
          subTitle="This feature is currently behind a feature flag and is not enabled."
        />
      </Layout>
    );
  }

  const canSubmit = form.name.trim() && form.dpo;

  const handleCreate = () => {
    if (!canSubmit) {
      return;
    }
    router.push(PRIVACY_ASSESSMENTS_ROUTE);
  };

  return (
    <Layout title="New assessment">
      <PageHeader
        heading="Privacy assessments"
        breadcrumbItems={[
          { title: "Privacy assessments", href: PRIVACY_ASSESSMENTS_ROUTE },
          { title: "New assessment" },
        ]}
      />

      <div style={{ maxWidth: 640 }}>
        <div
          style={{
            padding: "12px 16px",
            backgroundColor: palette.FIDESUI_BG_CORINTH,
            borderRadius: 8,
            marginBottom: 24,
          }}
        >
          <Text
            style={{
              fontSize: 14,
              lineHeight: 1.6,
              color: palette.FIDESUI_MINOS,
            }}
          >
            Your assessment will be pre-populated with data from your Fides data
            map, including system details, data categories, and processing
            purposes to give you a head start.
          </Text>
        </div>

        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Assessment name <span style={{ color: "red" }}>*</span>
            </Text>
            <Input
              placeholder="e.g., Customer Data Processing Assessment"
              value={form.name}
              onChange={(e) =>
                setForm((prev) => ({ ...prev, name: e.target.value }))
              }
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Framework / Template <span style={{ color: "red" }}>*</span>
            </Text>
            <Select
              style={{ width: "100%" }}
              aria-label="Select framework"
              value={form.framework}
              onChange={(value) =>
                setForm((prev) => ({ ...prev, framework: value }))
              }
              options={frameworks.map((f) => ({
                value: f.id,
                label: `${f.label} - ${f.description}`,
              }))}
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Assigned DPO / Owner <span style={{ color: "red" }}>*</span>
            </Text>
            <Select
              style={{ width: "100%" }}
              aria-label="Select DPO or owner"
              placeholder="Select a DPO or owner"
              value={form.dpo || undefined}
              onChange={(value) => setForm((prev) => ({ ...prev, dpo: value }))}
              options={dpoOptions.map((d) => ({
                value: d.id,
                label: `${d.name} - ${d.role}`,
              }))}
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              System
            </Text>
            <Select
              style={{ width: "100%" }}
              aria-label="Select system"
              placeholder="Select a system"
              value={form.systemName || undefined}
              onChange={(value) =>
                setForm((prev) => ({ ...prev, systemName: value }))
              }
              options={mockSystemNames.map((name) => ({
                value: name,
                label: name,
              }))}
            />
          </div>

          <div>
            <Text strong style={{ display: "block", marginBottom: 8 }}>
              Description
            </Text>
            <Input.TextArea
              placeholder="Brief description of the assessment purpose..."
              rows={3}
              value={form.description}
              onChange={(e) =>
                setForm((prev) => ({
                  ...prev,
                  description: e.target.value,
                }))
              }
            />
          </div>
        </Space>

        <Flex gap="middle" style={{ marginTop: 24 }}>
          <Button type="primary" disabled={!canSubmit} onClick={handleCreate}>
            Create assessment
          </Button>
          <Button onClick={() => router.push(PRIVACY_ASSESSMENTS_ROUTE)}>
            Cancel
          </Button>
        </Flex>
      </div>
    </Layout>
  );
};

export default NewAssessmentPage;
