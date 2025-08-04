/**
 * Template Engine for Jira Integration
 * Processes template variables and date math operations
 */

export interface DSRContext {
  requestId: string;
  requestType: "access" | "erasure";
  requestDate: string; // ISO date string
  dataSubject: string; // email
  subjectName?: string;
  fidesRequestUrl: string;
  adminDashboardUrl: string;
  affectedSystems: string[];
  estimatedCompletion: string;
  organization: string;
  privacyTeamEmail: string;
  dpoEmail?: string;
  regulation: "GDPR" | "CCPA" | "PIPEDA" | "Other";
  legalDueDate?: string; // ISO date string
}

export interface TemplateVariables {
  [key: string]: string | number | string[] | undefined;
}

/**
 * Calculate legal due date based on request type and regulation
 */
export const calculateDueDate = (
  requestType: string,
  regulation: string,
): string => {
  const today = new Date();
  let daysToAdd = 30; // Default

  switch (regulation) {
    case "GDPR":
      daysToAdd = requestType === "access" ? 30 : 30; // 1 month for most requests
      break;
    case "CCPA":
      daysToAdd = 45; // 45 days
      break;
    case "PIPEDA":
      daysToAdd = 30; // 30 days
      break;
    default:
      daysToAdd = 30;
  }

  const dueDate = new Date(today.getTime() + daysToAdd * 24 * 60 * 60 * 1000);
  return dueDate.toISOString().split("T")[0];
};

/**
 * Generate template variables from DSR context
 */
export const generateTemplateVariables = (
  context: DSRContext,
): TemplateVariables => {
  const today = new Date().toISOString().split("T")[0];
  const tomorrow = new Date(Date.now() + 24 * 60 * 60 * 1000)
    .toISOString()
    .split("T")[0];

  return {
    // Request Info
    "request-id": context.requestId,
    "request-type": context.requestType,
    "request-date": context.requestDate.split("T")[0],
    "data-subject": context.dataSubject,
    "subject-name": context.subjectName || context.dataSubject,

    // Fides Links
    "fides-dsr-link": context.fidesRequestUrl,
    "admin-dashboard-link": context.adminDashboardUrl,

    // Dates & Time
    today,
    tomorrow,
    "due-date":
      context.legalDueDate?.split("T")[0] ||
      calculateDueDate(context.requestType, context.regulation),

    // Organization Info
    organization: context.organization,
    "dpo-email": context.dpoEmail || context.privacyTeamEmail,
    "privacy-team": context.privacyTeamEmail,

    // Request Details
    "affected-systems": context.affectedSystems.join(", "),
    "estimated-completion": context.estimatedCompletion,
    regulation: context.regulation,
  };
};

/**
 * Process date math operations (e.g., "{{today}}+45", "{{due-date}}-7")
 */
export const processDateMath = (
  formula: string,
  variables: TemplateVariables,
): string => {
  // Match patterns like {{date}}+30 or {{date}}-7
  const mathPattern = /\{\{([^}]+)\}\}([+-]\d+)?/g;

  return formula.replace(mathPattern, (match, variableName, operation) => {
    const baseValue = variables[variableName];

    if (typeof baseValue !== "string") {
      return match; // Return original if not a string
    }

    // Check if it's a date (YYYY-MM-DD format)
    const datePattern = /^\d{4}-\d{2}-\d{2}$/;
    if (!datePattern.test(baseValue)) {
      return baseValue; // Return as-is if not a date
    }

    if (!operation) {
      return baseValue; // No math operation
    }

    const baseDate = new Date(`${baseValue}T00:00:00.000Z`);
    const operator = operation[0];
    const days = parseInt(operation.slice(1), 10);

    if (operator === "+") {
      baseDate.setUTCDate(baseDate.getUTCDate() + days);
    } else if (operator === "-") {
      baseDate.setUTCDate(baseDate.getUTCDate() - days);
    }

    return baseDate.toISOString().split("T")[0];
  });
};

/**
 * Process template string by replacing variables
 */
export const processTemplate = (
  template: string,
  context: DSRContext,
): string => {
  const variables = generateTemplateVariables(context);

  // First, process any date math formulas
  const processedTemplate = processDateMath(template, variables);

  // Then replace all template variables
  return processedTemplate.replace(
    /\{\{([^}]+)\}\}/g,
    (match, variableName) => {
      const value = variables[variableName.trim()];
      return value !== undefined ? String(value) : match;
    },
  );
};

/**
 * Preview template with example data
 */
export const generateTemplatePreview = (template: string): string => {
  const exampleContext: DSRContext = {
    requestId: "PR-12345",
    requestType: "erasure",
    requestDate: "2024-01-15T10:30:00Z",
    dataSubject: "user@example.com",
    subjectName: "John Doe",
    fidesRequestUrl: "https://fides.example.com/privacy-requests/PR-12345",
    adminDashboardUrl: "https://fides.example.com/privacy-requests",
    affectedSystems: ["PostgreSQL", "Salesforce", "S3"],
    estimatedCompletion: "15 business days",
    organization: "Example Corp",
    privacyTeamEmail: "privacy@example.com",
    dpoEmail: "dpo@example.com",
    regulation: "GDPR",
    legalDueDate: "2024-02-14T23:59:59Z",
  };

  return processTemplate(template, exampleContext);
};

/**
 * Validate template syntax
 */
export const validateTemplate = (template: string): string[] => {
  const errors: string[] = [];
  const variables = generateTemplateVariables({} as DSRContext);
  const validVariables = Object.keys(variables);

  // Find all template variables
  const variablePattern = /\{\{([^}]+)\}\}/g;
  let match = variablePattern.exec(template);

  while (match !== null) {
    const variableName = match[1].trim();

    // Check for date math operations
    const mathMatch = variableName.match(/^([^+-]+)([+-]\d+)?$/);
    if (mathMatch) {
      const baseVariable = mathMatch[1].trim();
      if (!validVariables.includes(baseVariable)) {
        errors.push(`Unknown variable: {{${baseVariable}}}`);
      }
    } else if (!validVariables.includes(variableName)) {
      errors.push(`Unknown variable: {{${variableName}}}`);
    }

    match = variablePattern.exec(template);
  }

  return errors;
};

/**
 * Get list of available template variables
 */
export const getAvailableVariables = (): {
  name: string;
  description: string;
  example: string;
}[] => {
  return [
    {
      name: "{{request-id}}",
      description: "Unique request identifier",
      example: "PR-12345",
    },
    {
      name: "{{request-type}}",
      description: "Type of privacy request",
      example: "erasure",
    },
    {
      name: "{{data-subject}}",
      description: "Data subject email address",
      example: "user@example.com",
    },
    {
      name: "{{subject-name}}",
      description: "Data subject full name",
      example: "John Doe",
    },
    {
      name: "{{request-date}}",
      description: "When request was submitted",
      example: "2024-01-15",
    },
    { name: "{{today}}", description: "Current date", example: "2024-01-15" },
    {
      name: "{{due-date}}",
      description: "Legal compliance due date",
      example: "2024-02-14",
    },
    {
      name: "{{fides-dsr-link}}",
      description: "Link to request in Fides",
      example: "https://fides.example.com/...",
    },
    {
      name: "{{admin-dashboard-link}}",
      description: "Link to admin dashboard",
      example: "https://fides.example.com/...",
    },
    {
      name: "{{affected-systems}}",
      description: "List of systems containing data",
      example: "PostgreSQL, Salesforce",
    },
    {
      name: "{{organization}}",
      description: "Organization name",
      example: "Example Corp",
    },
    {
      name: "{{privacy-team}}",
      description: "Privacy team contact email",
      example: "privacy@example.com",
    },
    {
      name: "{{regulation}}",
      description: "Applicable privacy regulation",
      example: "GDPR",
    },
    {
      name: "{{today}}+30",
      description: "30 days from today",
      example: "2024-02-14",
    },
    {
      name: "{{due-date}}-7",
      description: "7 days before due date",
      example: "2024-02-07",
    },
  ];
};
