import {
    AntButton as Button,
    AntForm as Form,
    AntInput as Input,
    AntSelect as Select,
    AntSteps as Steps,
    Box,
    Flex,
    Text,
    Textarea,
    VStack,
} from "fidesui";
import { useState } from "react";

interface JiraConfigFormData {
    // Connection
    instanceUrl: string;
    authType: "api_token" | "oauth2";
    username: string;
    apiToken: string;

    // Project Settings
    projectKey: string;
    issueType: string;
    defaultPriority: string;
    defaultAssignee?: string;
    defaultLabels: string[];

    // Templating
    titleTemplate: string;
    descriptionTemplate: string;
    dueDateFormula: string;
}

const DEFAULT_TITLE_TEMPLATE =
    "DSR Request: {{request-type}} for {{data-subject}}";

const DEFAULT_DESCRIPTION_TEMPLATE = `# Data Subject Request

**Request Details:**
- **Type:** {{request-type}}
- **Subject:** {{data-subject}} ({{subject-name}})
- **Submitted:** {{request-date}}
- **Request ID:** {{request-id}}

**Fides Dashboard:** {{fides-dsr-link}}

**Affected Systems:** {{affected-systems}}

**Estimated Completion:** {{estimated-completion}}

**Due Date:** {{due-date}}

---

**Next Steps:**
1. Review request details
2. Verify data subject identity
3. Process request across systems
4. Provide response to data subject

**Contact:** {{privacy-team}} for questions`;

const TEMPLATE_VARIABLES = [
    { label: "Request ID", value: "{{request-id}}" },
    { label: "Request Type", value: "{{request-type}}" },
    { label: "Data Subject Email", value: "{{data-subject}}" },
    { label: "Subject Name", value: "{{subject-name}}" },
    { label: "Request Date", value: "{{request-date}}" },
    { label: "Today's Date", value: "{{today}}" },
    { label: "Due Date", value: "{{due-date}}" },
    { label: "Fides DSR Link", value: "{{fides-dsr-link}}" },
    { label: "Admin Dashboard", value: "{{admin-dashboard-link}}" },
    { label: "Affected Systems", value: "{{affected-systems}}" },
    { label: "Organization", value: "{{organization}}" },
    { label: "Privacy Team Email", value: "{{privacy-team}}" },
    { label: "Regulation", value: "{{regulation}}" },
];

const DATE_FORMULA_EXAMPLES = [
    { label: "Today", value: "{{today}}" },
    { label: "30 days from today", value: "{{today}}+30" },
    { label: "45 days from today", value: "{{today}}+45" },
    { label: "Legal due date", value: "{{due-date}}" },
    { label: "7 days before due", value: "{{due-date}}-7" },
    { label: "30 days from request", value: "{{request-date}}+30" },
];

const JiraConfigurationForm = () => {
    const [form] = Form.useForm<JiraConfigFormData>();
    const [currentStep, setCurrentStep] = useState(0);
    const [testConnection, setTestConnection] = useState(false);

    const handleTestConnection = async () => {
        setTestConnection(true);
        // TODO: Implement connection test
        setTimeout(() => setTestConnection(false), 2000);
    };

    const insertTemplate = (field: any, template: string) => {
        const currentValue = form.getFieldValue(field) || "";
        const newValue = currentValue + template;
        form.setFieldValue(field, newValue);
    };

    const handleNext = async () => {
        try {
            // Validate current step fields before proceeding
            if (currentStep === 0) {
                await form.validateFields([
                    "instanceUrl",
                    "authType",
                    "username",
                    "apiToken",
                ]);
            }
            setCurrentStep(currentStep + 1);
        } catch (error) {
            // Validation failed, don't proceed
        }
    };

    const handlePrevious = () => {
        setCurrentStep(currentStep - 1);
    };

    const handleSubmit = async (values: JiraConfigFormData) => {
        console.log("Jira Configuration:", values);
        // TODO: Submit to API
    };

    const steps = [
        {
            title: "Connection",
            description: "Configure Jira connection",
        },
        {
            title: "Configuration",
            description: "Project and template settings",
        },
    ];

    const renderConnectionStep = () => (
        <VStack spacing={6} align="stretch">
            <Text fontSize="lg" fontWeight="semibold">
                Connection Settings
            </Text>

            <Form.Item
                label="Jira Instance URL"
                name="instanceUrl"
                rules={[
                    { required: true, message: "Instance URL is required" },
                    { type: "url", message: "Please enter a valid URL" },
                ]}
            >
                <Input placeholder="https://your-company.atlassian.net" />
            </Form.Item>

            <Form.Item label="Authentication Type" name="authType">
                <Select
                    options={[
                        { value: "api_token", label: "API Token" },
                        { value: "oauth2", label: "OAuth 2.0" },
                    ]}
                />
            </Form.Item>

            <Form.Item
                label="Username/Email"
                name="username"
                rules={[{ required: true, message: "Username is required" }]}
            >
                <Input placeholder="your-email@company.com" />
            </Form.Item>

            <Form.Item
                label="API Token"
                name="apiToken"
                rules={[{ required: true, message: "API Token is required" }]}
            >
                <Input.Password placeholder="Your Jira API token" />
            </Form.Item>

            <Button
                onClick={handleTestConnection}
                loading={testConnection}
                style={{ alignSelf: "flex-start" }}
            >
                Test Connection
            </Button>
        </VStack>
    );

    const renderConfigurationStep = () => (
        <VStack spacing={6} align="stretch">
            {/* Project Configuration */}
            <Box>
                <Text fontSize="lg" fontWeight="semibold" mb={4}>
                    Project Configuration
                </Text>

                <VStack spacing={4} align="stretch">
                    <Form.Item
                        label="Project Key"
                        name="projectKey"
                        rules={[{ required: true, message: "Project key is required" }]}
                    >
                        <Input placeholder="PRIV" />
                    </Form.Item>

                    <Form.Item
                        label="Issue Type"
                        name="issueType"
                        rules={[{ required: true, message: "Issue type is required" }]}
                    >
                        <Select
                            placeholder="Select issue type"
                            options={[
                                { value: "Task", label: "Task" },
                                { value: "Story", label: "Story" },
                                { value: "Bug", label: "Bug" },
                                { value: "Epic", label: "Epic" },
                            ]}
                        />
                    </Form.Item>

                    <Form.Item label="Default Priority" name="defaultPriority">
                        <Select
                            options={[
                                { value: "Highest", label: "Highest" },
                                { value: "High", label: "High" },
                                { value: "Medium", label: "Medium" },
                                { value: "Low", label: "Low" },
                                { value: "Lowest", label: "Lowest" },
                            ]}
                        />
                    </Form.Item>

                    <Form.Item label="Default Assignee" name="defaultAssignee">
                        <Input placeholder="user@company.com or leave empty for unassigned" />
                    </Form.Item>

                    <Form.Item label="Default Labels" name="defaultLabels">
                        <Select
                            mode="tags"
                            placeholder="Add labels"
                            options={[
                                { value: "privacy", label: "privacy" },
                                { value: "dsr", label: "dsr" },
                                { value: "gdpr", label: "gdpr" },
                                { value: "ccpa", label: "ccpa" },
                            ]}
                        />
                    </Form.Item>
                </VStack>
            </Box>

            {/* Template Configuration */}
            <Box>
                <Text fontSize="lg" fontWeight="semibold" mb={4}>
                    Template Configuration
                </Text>

                <VStack spacing={4} align="stretch">
                    <Box>
                        <Text fontSize="sm" fontWeight="medium" mb={2}>
                            Available Variables:
                        </Text>
                        <Flex wrap="wrap" gap={2}>
                            {TEMPLATE_VARIABLES.map((variable) => (
                                <Button
                                    key={variable.value}
                                    size="small"
                                    onClick={() =>
                                        insertTemplate("titleTemplate", variable.value)
                                    }
                                    style={{ fontSize: "11px", padding: "2px 6px" }}
                                >
                                    {variable.value}
                                </Button>
                            ))}
                        </Flex>
                    </Box>

                    <Form.Item
                        label="Ticket Title Template"
                        name="titleTemplate"
                        rules={[{ required: true, message: "Title template is required" }]}
                    >
                        <Input placeholder="DSR Request: {{request-type}} for {{data-subject}}" />
                    </Form.Item>

                    <Form.Item
                        label="Ticket Description Template"
                        name="descriptionTemplate"
                        rules={[
                            { required: true, message: "Description template is required" },
                        ]}
                    >
                        <Textarea
                            rows={8}
                            placeholder="Enter your description template with variables..."
                        />
                    </Form.Item>

                    <Box>
                        <Text fontSize="sm" fontWeight="medium" mb={2}>
                            Date Formula Examples:
                        </Text>
                        <Flex wrap="wrap" gap={2}>
                            {DATE_FORMULA_EXAMPLES.map((formula) => (
                                <Button
                                    key={formula.value}
                                    size="small"
                                    onClick={() =>
                                        form.setFieldValue("dueDateFormula", formula.value)
                                    }
                                    style={{ fontSize: "11px", padding: "2px 6px" }}
                                >
                                    {formula.label}
                                </Button>
                            ))}
                        </Flex>
                    </Box>

                    <Form.Item
                        label="Due Date Formula"
                        name="dueDateFormula"
                        extra="Use formulas like {{today}}+45 for 45 days from today, or {{due-date}}-7 for 7 days before legal deadline"
                    >
                        <Input placeholder="{{today}}+45" />
                    </Form.Item>
                </VStack>
            </Box>
        </VStack>
    );

    return (
        <Box maxWidth="800px" mx="auto" p={6}>
            <Text fontSize="xl" fontWeight="bold" mb={6}>
                Configure Jira Integration
            </Text>

            <Steps current={currentStep} items={steps} style={{ marginBottom: 32 }} />

            <Form
                form={form}
                layout="vertical"
                onFinish={handleSubmit}
                initialValues={{
                    authType: "api_token",
                    defaultPriority: "Medium",
                    titleTemplate: DEFAULT_TITLE_TEMPLATE,
                    descriptionTemplate: DEFAULT_DESCRIPTION_TEMPLATE,
                    dueDateFormula: "{{today}}+45",
                    defaultLabels: ["privacy", "dsr"],
                }}
            >
                {currentStep === 0 && renderConnectionStep()}
                {currentStep === 1 && renderConfigurationStep()}

                <Flex justify="space-between" mt={8}>
                    <Button
                        onClick={handlePrevious}
                        disabled={currentStep === 0}
                        style={{ visibility: currentStep === 0 ? "hidden" : "visible" }}
                    >
                        Previous
                    </Button>

                    <Flex gap={3}>
                        {currentStep < steps.length - 1 ? (
                            <Button type="primary" onClick={handleNext}>
                                Next
                            </Button>
                        ) : (
                            <Button type="primary" htmlType="submit">
                                Save Configuration
                            </Button>
                        )}
                    </Flex>
                </Flex>
            </Form>
        </Box>
    );
};

export default JiraConfigurationForm;
