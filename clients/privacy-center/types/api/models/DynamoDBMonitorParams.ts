/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

export type DynamoDBMonitorParams = {
  /**
   * Whether the DynamoDB monitor should put all tables found in Dynamo into a single Fides Dataset, or one Dataset per Dynamo table
   */
  single_dataset?: boolean | null;
};
