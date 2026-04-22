import {
  Checkbox,
  Divider,
  Flex,
  Form,
  Radio,
  Switch,
  Typography,
} from "fidesui";
import { ReactNode } from "react";

import { useAppSelector } from "~/app/hooks";
import { useFeatures } from "~/features/common/features";
import { selectGppSettings } from "~/features/config-settings/config-settings.slice";
import { GPPUSApproach, PrivacyExperienceGPPSettings } from "~/types/api";

import FrameworkStatus from "./FrameworkStatus";
import SettingsBox from "./SettingsBox";

const Section = ({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) => (
  <Flex vertical gap="middle" className="mb-3" data-testid={`section-${title}`}>
    <Typography.Text strong className="text-sm">
      {title}
    </Typography.Text>
    {children}
  </Flex>
);

const GppConfiguration = () => {
  const { tcf: isTcfEnabled } = useFeatures();
  const gppSettings = useAppSelector(selectGppSettings);
  const isEnabled = !!gppSettings.enabled;
  const form = Form.useFormInstance<{
    gpp: PrivacyExperienceGPPSettings;
  }>();
  const gppValues = Form.useWatch("gpp", form);
  const showMspa = !!gppValues?.us_approach;

  return (
    <SettingsBox title="Global Privacy Platform">
      <Flex vertical gap="large">
        <FrameworkStatus name="GPP" enabled={isEnabled} />
        {isEnabled ? (
          <>
            <Section title="GPP U.S.">
              <Form.Item name={["gpp", "us_approach"]} noStyle>
                <Radio.Group data-testid="input-gpp.us_approach">
                  <Flex vertical gap="middle">
                    <Radio
                      value={GPPUSApproach.NATIONAL}
                      data-testid={`option-${GPPUSApproach.NATIONAL}`}
                    >
                      <Flex align="center" gap="small">
                        <Typography.Text className="text-sm font-medium">
                          Enable U.S. National
                        </Typography.Text>
                        <Form.Item
                          tooltip="When US National is selected, Fides will present the same privacy notices to all consumers located anywhere in the United States."
                          noStyle
                        >
                          <span />
                        </Form.Item>
                      </Flex>
                    </Radio>
                    <Radio
                      value={GPPUSApproach.STATE}
                      data-testid={`option-${GPPUSApproach.STATE}`}
                    >
                      <Flex align="center" gap="small">
                        <Typography.Text className="text-sm font-medium">
                          Enable U.S. State-by-State
                        </Typography.Text>
                        <Form.Item
                          tooltip="When state-by-state is selected, Fides will only present consent to consumers and save their preferences if they are located in a state that is supported by the GPP. The consent options presented to consumers will vary depending on the regulations in each state."
                          noStyle
                        >
                          <span />
                        </Form.Item>
                      </Flex>
                    </Radio>
                    <Radio
                      value={GPPUSApproach.ALL}
                      data-testid={`option-${GPPUSApproach.ALL}`}
                    >
                      <Flex align="center" gap="small">
                        <Typography.Text className="text-sm font-medium">
                          Enable US National and State-by-State notices
                        </Typography.Text>
                        <Form.Item
                          tooltip="When enabled, Fides can be configured to serve the National and U.S. state notices. This mode is intended to provide consent coverage to U.S. states with new privacy laws where GPP support lags behind the effective date of state laws."
                          noStyle
                        >
                          <span />
                        </Form.Item>
                      </Flex>
                    </Radio>
                  </Flex>
                </Radio.Group>
              </Form.Item>
            </Section>
            {showMspa ? (
              <Section title="MSPA">
                <Form.Item
                  name={["gpp", "mspa_covered_transactions"]}
                  valuePropName="checked"
                  tooltip="When selected, the Fides CMP will communicate to downstream vendors that all preferences are covered under the MSPA."
                >
                  <Checkbox
                    data-testid="input-gpp.mspa_covered_transactions"
                    onChange={(e) => {
                      if (!e.target.checked) {
                        form.setFieldValue(
                          ["gpp", "mspa_service_provider_mode"],
                          false,
                        );
                        form.setFieldValue(
                          ["gpp", "mspa_opt_out_option_mode"],
                          false,
                        );
                      }
                    }}
                  >
                    All transactions covered by MSPA
                  </Checkbox>
                </Form.Item>
                <Form.Item
                  name={["gpp", "mspa_service_provider_mode"]}
                  label="Enable MSPA service provider mode"
                  tooltip="Enable service provider mode if you do not engage in any sales or sharing of personal information."
                  layout="horizontal"
                  colon={false}
                  valuePropName="checked"
                >
                  <Switch
                    size="small"
                    disabled={
                      !!gppValues?.mspa_opt_out_option_mode ||
                      !gppValues?.mspa_covered_transactions
                    }
                    data-testid="input-gpp.mspa_service_provider_mode"
                  />
                </Form.Item>
                <Form.Item
                  name={["gpp", "mspa_opt_out_option_mode"]}
                  label="Enable MSPA opt-out option mode"
                  tooltip="Enable opt-out option mode if you engage or may engage in the sales or sharing of personal information, or process any information for the purpose of targeted advertising."
                  layout="horizontal"
                  colon={false}
                  valuePropName="checked"
                >
                  <Switch
                    size="small"
                    disabled={
                      !!gppValues?.mspa_service_provider_mode ||
                      !gppValues?.mspa_covered_transactions
                    }
                    data-testid="input-gpp.mspa_opt_out_option_mode"
                  />
                </Form.Item>
              </Section>
            ) : null}
          </>
        ) : null}
        {isTcfEnabled ? (
          <>
            <Divider className="my-0" />
            <Section title="GPP Europe">
              <Typography.Text className="text-sm font-medium">
                Configure TCF string for Global Privacy Platform
              </Typography.Text>
              <Form.Item
                name={["gpp", "enable_tcfeu_string"]}
                label="Enable TC string"
                tooltip="When enabled, the GPP API will include a TCF EU consent string for users who are in regions where TCF applies."
                layout="horizontal"
                colon={false}
                valuePropName="checked"
              >
                <Switch
                  size="small"
                  data-testid="input-gpp.enable_tcfeu_string"
                />
              </Form.Item>
            </Section>
          </>
        ) : null}
      </Flex>
    </SettingsBox>
  );
};

export default GppConfiguration;
