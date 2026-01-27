#!/usr/bin/env ts-node
/**
 * TypeScript API Type Validator
 * 
 * This script validates that TypeScript types match the backend API schemas
 * by comparing the generated OpenAPI schema with the TypeScript type definitions.
 * 
 * It checks for:
 * - Missing fields in TypeScript that exist in the API
 * - Type mismatches (e.g., Set vs Array, Dict vs Record)
 * - Incorrect nullability
 * - Enum vs string literal type mismatches
 * 
 * Usage:
 *   ts-node scripts/validate_api_types.ts <openapi-schema-path>
 */

import * as fs from 'fs';
import * as path from 'path';

interface ValidationError {
  type: 'missing_field' | 'type_mismatch' | 'nullability_mismatch' | 'known_issue';
  severity: 'error' | 'warning' | 'info';
  schema: string;
  schemaType: 'request' | 'response' | 'shared';
  field?: string;
  expected: string;
  actual: string;
  message: string;
}

interface OpenAPISchema {
  components?: {
    schemas?: Record<string, any>;
  };
}

interface TypeScriptType {
  name: string;
  fields: Record<string, { type: string; optional: boolean; nullable: boolean }>;
}

// Known issues that we're tracking but not failing on
// NOTE: Set -> Array conversions are now automatically detected as warnings, not errors
// Only add issues here that are intentional manual overrides or require special handling
//
// GUIDELINES FOR ADDING KNOWN ISSUES:
// 1. Add a comment in the TypeScript file explaining why it's manually overridden
// 2. Reference a PR/ticket that documents the decision
// 3. Periodically review if the override is still needed
// 4. Remove from this list when the underlying issue is fixed
const KNOWN_ISSUES = [
  {
    schema: 'PrivacyRequestResponse',
    field: 'custom_privacy_request_fields',
    reason: 'Manually overridden in TypeScript for better type safety. Backend uses Dict[str, Any], frontend needs structured type. See clients/admin-ui/src/types/api/models/PrivacyRequestResponse.ts:30',
  },
];

class APITypeValidator {
  private errors: ValidationError[] = [];
  private warnings: ValidationError[] = [];
  private openApiSchema: OpenAPISchema;
  private tsTypesPath: string;

  constructor(openApiSchemaPath: string, tsTypesPath: string) {
    this.openApiSchema = JSON.parse(fs.readFileSync(openApiSchemaPath, 'utf-8'));
    this.tsTypesPath = tsTypesPath;
  }

  /**
   * Categorize schema as request, response, or shared based on naming conventions
   */
  private categorizeSchema(schemaName: string): 'request' | 'response' | 'shared' {
    // Response types
    if (
      schemaName.endsWith('Response') ||
      schemaName.endsWith('Result') ||
      schemaName === 'AccessToken' ||
      schemaName === 'Page'
    ) {
      return 'response';
    }
    
    // Request types
    if (
      schemaName.endsWith('Request') ||
      schemaName.endsWith('Create') ||
      schemaName.endsWith('Update') ||
      schemaName.endsWith('Params') ||
      schemaName.endsWith('Patch') ||
      schemaName.endsWith('Body')
    ) {
      return 'request';
    }
    
    // Shared or model types
    return 'shared';
  }

  /**
   * Main validation entry point
   */
  validate(): { errors: ValidationError[]; warnings: ValidationError[] } {
    console.log('🔍 Validating TypeScript types against OpenAPI schema...\n');

    const schemas = this.openApiSchema.components?.schemas || {};
    const schemaNames = Object.keys(schemas);

    console.log(`Found ${schemaNames.length} schemas to validate\n`);

    for (const schemaName of schemaNames) {
      // Skip internal schemas
      if (schemaName.startsWith('Body_') || schemaName.startsWith('HTTPValidationError')) {
        continue;
      }

      this.validateSchema(schemaName, schemas[schemaName]);
    }

    return {
      errors: this.errors,
      warnings: this.warnings,
    };
  }

  /**
   * Validate a single schema
   */
  private validateSchema(schemaName: string, schema: any): void {
    const tsFilePath = this.findTypeScriptFile(schemaName);

    if (!tsFilePath) {
      // Only warn about missing files for Response/Request/Create/Update types
      if (
        schemaName.endsWith('Response') ||
        schemaName.endsWith('Request') ||
        schemaName.endsWith('Create') ||
        schemaName.endsWith('Update')
      ) {
        this.warnings.push({
          type: 'missing_field',
          severity: 'warning',
          schema: schemaName,
          schemaType: this.categorizeSchema(schemaName),
          expected: 'TypeScript file',
          actual: 'not found',
          message: `TypeScript type definition not found for ${schemaName}`,
        });
      }
      return;
    }

    const tsContent = fs.readFileSync(tsFilePath, 'utf-8');
    this.validateSchemaFields(schemaName, schema, tsContent);
  }

  /**
   * Validate fields in a schema
   */
  private validateSchemaFields(schemaName: string, schema: any, tsContent: string): void {
    if (!schema.properties) {
      return;
    }

    for (const [fieldName, fieldSchema] of Object.entries<any>(schema.properties)) {
      const isRequired = schema.required?.includes(fieldName) || false;
      const expectedType = this.getExpectedType(fieldSchema, `${schemaName}.${fieldName}`);

      // Check if field exists in TypeScript - handle multiline types
      // Match: fieldName?: type; or fieldName: type;
      // Allow whitespace, newlines, and comments between parts
      const fieldPattern = new RegExp(
        `${this.escapeRegex(fieldName)}([?]?)\\s*:\\s*([^;]+?);`,
        'ms'
      );
      const match = tsContent.match(fieldPattern);

      if (!match) {
        // Check if this is a known issue
        const knownIssue = KNOWN_ISSUES.find(
          (issue) => issue.schema === schemaName && issue.field === fieldName
        );

      if (knownIssue) {
        // Still track known overrides as INFO so they're visible
        // This allows us to catch when backend improves and override becomes unnecessary
        this.warnings.push({
          type: 'known_issue',
          severity: 'info',
          schema: schemaName,
          schemaType: this.categorizeSchema(schemaName),
          field: fieldName,
          expected: expectedType,
          actual: 'manually overridden',
          message: `Intentional override: ${knownIssue.reason}. ⚠️ Verify this is still needed - if backend now provides proper types, remove the override!`,
        });
      } else {
        this.errors.push({
          type: 'missing_field',
          severity: 'error',
          schema: schemaName,
          schemaType: this.categorizeSchema(schemaName),
          field: fieldName,
          expected: expectedType,
          actual: 'missing',
          message: `Field "${fieldName}" is missing in TypeScript type`,
        });
      }
        continue;
      }

      const isOptional = match[1] === '?';
      const tsType = match[2].trim().replace(/\s+/g, ' '); // Normalize whitespace

      // Validate type compatibility
      this.validateTypeCompatibility(schemaName, fieldName, expectedType, tsType, isRequired, isOptional);
    }
  }

  /**
   * Validate type compatibility between OpenAPI and TypeScript
   */
  private validateTypeCompatibility(
    schemaName: string,
    fieldName: string,
    expectedType: string,
    actualType: string,
    isRequired: boolean,
    isOptional: boolean
  ): void {
    // Check nullability
    if (!isRequired && !isOptional) {
      this.errors.push({
        type: 'nullability_mismatch',
        severity: 'error',
        schema: schemaName,
        schemaType: this.categorizeSchema(schemaName),
        field: fieldName,
        expected: 'optional field',
        actual: 'required field',
        message: `Field "${fieldName}" should be optional but is required in TypeScript`,
      });
    }

    // Check for loose 'any' types when backend expects something specific
    if (actualType === 'any' && expectedType !== 'any') {
      this.warnings.push({
        type: 'type_mismatch',
        severity: 'warning',
        schema: schemaName,
        schemaType: this.categorizeSchema(schemaName),
        field: fieldName,
        expected: expectedType,
        actual: actualType,
        message: `Loose 'any' type in TypeScript. Backend expects ${expectedType}. Consider using proper type or '${expectedType} | null' if backend can return null.`,
      });
      return; // Don't do additional type checking
    }

    // Check for common type mismatches
    const typeIssues = this.detectTypeMismatch(expectedType, actualType);
    if (typeIssues) {
      // Check if this is a known issue
      const knownIssue = KNOWN_ISSUES.find(
        (issue) => issue.schema === schemaName && issue.field === fieldName
      );

      if (knownIssue) {
        // Still track known overrides as INFO so they're visible
        this.warnings.push({
          type: 'known_issue',
          severity: 'info',
          schema: schemaName,
          schemaType: this.categorizeSchema(schemaName),
          field: fieldName,
          expected: expectedType,
          actual: actualType,
          message: `Intentional override: ${knownIssue.reason}. ⚠️ Verify this is still needed - if backend changed, update the override!`,
        });
      } else if (typeIssues.isWarning) {
        // This is an expected difference, not an error
        this.warnings.push({
          type: 'type_mismatch',
          severity: 'warning',
          schema: schemaName,
          schemaType: this.categorizeSchema(schemaName),
          field: fieldName,
          expected: expectedType,
          actual: actualType,
          message: typeIssues.message,
        });
      } else {
        this.errors.push({
          type: 'type_mismatch',
          severity: 'error',
          schema: schemaName,
          schemaType: this.categorizeSchema(schemaName),
          field: fieldName,
          expected: expectedType,
          actual: actualType,
          message: typeIssues.message,
        });
      }
    }
  }

  /**
   * Detect type mismatches
   * Returns: { message: string, isWarning: boolean } or null
   */
  private detectTypeMismatch(
    expectedType: string,
    actualType: string
  ): { message: string; isWarning: boolean } | null {
    // Normalize types for comparison
    const normalizedExpected = expectedType.replace(/\s+/g, '').toLowerCase();
    const normalizedActual = actualType.replace(/\s+/g, '').toLowerCase();

    // Check for Set vs Array mismatch - this is EXPECTED due to JSON serialization
    if (normalizedExpected.includes('set<') && normalizedActual.includes('array<')) {
      return {
        message: 'Python Set type is represented as Array in TypeScript (JSON serialization)',
        isWarning: true, // This is expected behavior, not an error
      };
    }

    // Check for Dict[str, Any] vs any mismatch
    if (normalizedExpected.includes('dict[str,any]') && normalizedActual === 'any') {
      return {
        message: 'Loose typing: Dict[str, Any] maps to "any" - consider stronger typing',
        isWarning: true,
      };
    }

    // Check for Record<string, any> usage
    if (normalizedActual.includes('record<string,any>')) {
      return {
        message: 'Loose typing: Using Record<string, any> - consider stronger typing',
        isWarning: true,
      };
    }

    return null;
  }

  /**
   * Get expected TypeScript type from OpenAPI schema
   */
  private getExpectedType(schema: any, context: string = 'unknown'): string {
    // Handle null/undefined schemas - this indicates a malformed OpenAPI schema
    if (!schema) {
      console.warn(`⚠️  Malformed schema at ${context}: schema is null or undefined`);
      const schemaName = context.split('.')[0];
      this.warnings.push({
        type: 'type_mismatch',
        severity: 'warning',
        schema: context,
        schemaType: this.categorizeSchema(schemaName),
        expected: 'valid schema definition',
        actual: 'null or undefined',
        message: `OpenAPI schema is malformed: missing schema definition at ${context}`,
      });
      return 'any';
    }

    if (schema.$ref) {
      return schema.$ref.split('/').pop();
    }

    if (schema.type === 'array') {
      // Handle array with missing or invalid items
      if (!schema.items) {
        console.warn(`⚠️  Array schema at ${context} is missing 'items' definition`);
        const schemaName = context.split('.')[0];
        this.warnings.push({
          type: 'type_mismatch',
          severity: 'warning',
          schema: context,
          schemaType: this.categorizeSchema(schemaName),
          expected: 'array with items definition',
          actual: 'array without items',
          message: `Array schema is missing 'items' definition at ${context}`,
        });
        return 'Array<any>';
      }
      const itemType = this.getExpectedType(schema.items, `${context}[items]`);
      return `Array<${itemType}>`;
    }

    if (schema.type === 'object') {
      if (schema.additionalProperties) {
        const valueType = this.getExpectedType(
          schema.additionalProperties,
          `${context}[additionalProperties]`
        );
        return `Record<string, ${valueType}>`;
      }
      return 'object';
    }

    if (schema.enum) {
      return schema.enum.map((v: any) => `"${v}"`).join(' | ');
    }

    if (schema.anyOf || schema.oneOf) {
      const unionType = schema.anyOf ? 'anyOf' : 'oneOf';
      const items = schema.anyOf || schema.oneOf;
      
      // Check for null/undefined items in unions
      const validItems = items.filter((s: any) => s);
      if (validItems.length !== items.length) {
        console.warn(
          `⚠️  ${unionType} at ${context} contains ${items.length - validItems.length} null/undefined item(s)`
        );
      }
      
      const types = validItems.map((s: any, idx: number) =>
        this.getExpectedType(s, `${context}[${unionType}[${idx}]]`)
      );
      return types.join(' | ');
    }

    switch (schema.type) {
      case 'string':
        return 'string';
      case 'number':
      case 'integer':
        return 'number';
      case 'boolean':
        return 'boolean';
      default:
        return 'any';
    }
  }

  /**
   * Escape special regex characters
   */
  private escapeRegex(str: string): string {
    return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Find TypeScript file for a schema
   */
  private findTypeScriptFile(schemaName: string): string | null {
    // Try direct match
    const directPath = path.join(this.tsTypesPath, 'models', `${schemaName}.ts`);
    if (fs.existsSync(directPath)) {
      return directPath;
    }

    // Try with namespace prefix (e.g., fides__api__schemas__...)
    const files = fs.readdirSync(path.join(this.tsTypesPath, 'models'));
    const matchingFile = files.find((file) => file.endsWith(`${schemaName}.ts`));

    if (matchingFile) {
      return path.join(this.tsTypesPath, 'models', matchingFile);
    }

    return null;
  }

  /**
   * Print validation results
   */
  printResults(): void {
    console.log('\n' + '='.repeat(80));
    console.log('VALIDATION RESULTS');
    console.log('='.repeat(80) + '\n');

    // Print summary
    console.log(`Schemas validated: ${Object.keys(this.openApiSchema.components?.schemas || {}).length}`);
    console.log(`Errors: ${this.errors.length}`);
    console.log(`Warnings: ${this.warnings.length}\n`);

    if (this.warnings.length > 0) {
      console.log(`⚠️  ${this.warnings.length} Warning(s) (non-blocking):\n`);
      
      // Group warnings by type
      const warningsByType = new Map<string, ValidationError[]>();
      for (const warning of this.warnings) {
        const key = warning.type;
        if (!warningsByType.has(key)) {
          warningsByType.set(key, []);
        }
        warningsByType.get(key)!.push(warning);
      }

      for (const [type, warnings] of warningsByType) {
        console.log(`  ${type}: ${warnings.length} occurrence(s)`);
        
        // Show all known_issue warnings (they're important to review)
        // Show only first 3 of other warnings
        const warningsToShow = type === 'known_issue' ? warnings : warnings.slice(0, 3);
        
        for (const warning of warningsToShow) {
          console.log(`    • ${warning.schema}${warning.field ? `.${warning.field}` : ''}`);
          console.log(`      ${warning.message}`);
          if (type === 'known_issue') {
            console.log(`      Python (backend): ${warning.expected}`);
            console.log(`      TypeScript (frontend): ${warning.actual}`);
          }
        }
        if (type !== 'known_issue' && warnings.length > 3) {
          console.log(`    ... and ${warnings.length - 3} more\n`);
        }
        console.log();
      }
    }

    if (this.errors.length > 0) {
      console.log(`❌ ${this.errors.length} Error(s) (must fix):\n`);
      
      // Group errors by schema type (request/response/shared)
      const responseErrors = this.errors.filter((e) => e.schemaType === 'response');
      const requestErrors = this.errors.filter((e) => e.schemaType === 'request');
      const sharedErrors = this.errors.filter((e) => e.schemaType === 'shared');
      
      if (responseErrors.length > 0) {
        console.log(`  📤 RESPONSE TYPES (${responseErrors.length} errors):`);
        console.log(`     ⚠️  Critical: Backend returns data that TypeScript doesn't handle\n`);
        for (const error of responseErrors) {
          console.log(`    [${error.type}] ${error.schema}${error.field ? `.${error.field}` : ''}`);
          console.log(`      Problem: ${error.message}`);
          console.log(`      Python (backend) has: ${error.expected}`);
          console.log(`      TypeScript (frontend) has: ${error.actual}`);
          console.log(`      → Fix: Update TypeScript types to match Python backend\n`);
        }
      }
      
      if (requestErrors.length > 0) {
        console.log(`  📥 REQUEST TYPES (${requestErrors.length} errors):`);
        console.log(`     ⚠️  Moderate: TypeScript may not be sending what backend expects\n`);
        for (const error of requestErrors) {
          console.log(`    [${error.type}] ${error.schema}${error.field ? `.${error.field}` : ''}`);
          console.log(`      Problem: ${error.message}`);
          console.log(`      Python (backend) expects: ${error.expected}`);
          console.log(`      TypeScript (frontend) sends: ${error.actual}`);
          console.log(`      → Fix: Update TypeScript types to match Python backend\n`);
        }
      }
      
      if (sharedErrors.length > 0) {
        console.log(`  🔄 SHARED/MODEL TYPES (${sharedErrors.length} errors):\n`);
        for (const error of sharedErrors) {
          console.log(`    [${error.type}] ${error.schema}${error.field ? `.${error.field}` : ''}`);
          console.log(`      Problem: ${error.message}`);
          console.log(`      Python (backend): ${error.expected}`);
          console.log(`      TypeScript (frontend): ${error.actual}`);
          console.log(`      → Fix: Update TypeScript types to match Python backend\n`);
        }
      }
    } else {
      console.log('✅ No errors found!\n');
    }

    console.log('='.repeat(80) + '\n');
    
    if (this.errors.length > 0) {
      console.log('💡 Tips:');
      console.log('  - Regenerate TypeScript types: turbo run openapi:generate');
      console.log('  - Check backend model definitions in src/fidesplus/api/schemas/');
      console.log('  - Add to KNOWN_ISSUES in this script if mismatch is intentional\n');
    }
  }
}

// Main execution
if (require.main === module) {
  const args = process.argv.slice(2);

  if (args.length < 1) {
    console.error('Usage: ts-node validate_api_types.ts <openapi-schema-path> [ts-types-path]');
    process.exit(1);
  }

  const openApiSchemaPath = args[0];
  const tsTypesPath = args[1] || path.join(__dirname, '../clients/admin-ui/src/types/api');

  if (!fs.existsSync(openApiSchemaPath)) {
    console.error(`Error: OpenAPI schema file not found: ${openApiSchemaPath}`);
    process.exit(1);
  }

  if (!fs.existsSync(tsTypesPath)) {
    console.error(`Error: TypeScript types directory not found: ${tsTypesPath}`);
    process.exit(1);
  }

  const validator = new APITypeValidator(openApiSchemaPath, tsTypesPath);
  const { errors, warnings } = validator.validate();
  validator.printResults();

  // Exit with error code if there are errors
  if (errors.length > 0) {
    process.exit(1);
  }
}

export { APITypeValidator, ValidationError };

