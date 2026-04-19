import Head from "common/Head";
import Image from "common/Image";
import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Typography,
  useMessage,
} from "fidesui";
import type { NextPage } from "next";
import { useState } from "react";

import { useForgotPasswordMutation } from "~/features/auth";
import { getErrorMessage } from "~/features/common/helpers";
import { RouterLink } from "~/features/common/nav/RouterLink";
import { RTKErrorResult } from "~/types/errors/api";

interface ForgotPasswordFormValues {
  email: string;
}

const ForgotPassword: NextPage = () => {
  const [form] = Form.useForm<ForgotPasswordFormValues>();
  const [forgotPasswordRequest] = useForgotPasswordMutation();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [canSubmit, setCanSubmit] = useState(false);
  const message = useMessage();

  const handleSubmit = async (values: ForgotPasswordFormValues) => {
    setIsSubmitting(true);
    try {
      await forgotPasswordRequest({ email: values.email }).unwrap();
      setSubmitted(true);
    } catch (error) {
      const errorMsg = getErrorMessage(
        error as RTKErrorResult["error"],
        "Something went wrong. Please try again.",
      );
      message.error(errorMsg);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Flex className="w-full" justify="center">
      <Head />

      <main data-testid="ForgotPassword">
        <Flex
          vertical
          gap={64}
          align="center"
          justify="center"
          className="px-6 py-12"
        >
          <Image src="/logo.svg" alt="Fides logo" width={205} height={46} />
          <Flex vertical align="center" gap="large">
            <Typography.Title level={1}>
              {submitted ? "Check your email" : "Forgot your password?"}
            </Typography.Title>
            <Card className="static w-[640px] px-32 py-12">
              <Flex align="center" justify="center">
                {submitted ? (
                  <Flex vertical gap={16} align="center" className="w-full">
                    <Typography.Text className="text-center">
                      If an account with that email exists, we&apos;ve sent a
                      password reset link. Please check your inbox.
                    </Typography.Text>
                    <RouterLink href="/login">
                      <Button type="link" data-testid="back-to-login-btn">
                        Back to sign in
                      </Button>
                    </RouterLink>
                  </Flex>
                ) : (
                  <Form
                    form={form}
                    layout="vertical"
                    onFinish={handleSubmit}
                    onValuesChange={(
                      _: Partial<ForgotPasswordFormValues>,
                      allValues: ForgotPasswordFormValues,
                    ) => {
                      setCanSubmit(!!allValues.email);
                    }}
                    className="w-full"
                  >
                    <Flex vertical>
                      <Typography.Text className="mb-4">
                        Enter your email address and we&apos;ll send you a link
                        to reset your password.
                      </Typography.Text>
                      <Form.Item
                        name="email"
                        label="Email address"
                        rules={[
                          { required: true, message: "Email is required" },
                          {
                            type: "email",
                            message: "Please enter a valid email",
                          },
                        ]}
                      >
                        <Input
                          size="large"
                          data-testid="input-email"
                          autoComplete="email"
                          placeholder="Enter your email address"
                        />
                      </Form.Item>
                      <Button
                        htmlType="submit"
                        type="primary"
                        disabled={!canSubmit}
                        data-testid="send-reset-link-btn"
                        loading={isSubmitting}
                        className="w-full"
                      >
                        Send reset link
                      </Button>
                      <Flex justify="center" className="mt-4">
                        <RouterLink href="/login">
                          <Button type="link" data-testid="back-to-login-btn">
                            Back to sign in
                          </Button>
                        </RouterLink>
                      </Flex>
                    </Flex>
                  </Form>
                )}
              </Flex>
            </Card>
          </Flex>
        </Flex>
      </main>
    </Flex>
  );
};

export default ForgotPassword;
