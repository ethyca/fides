/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { DatastoreStagedResourceTreeAPIResponse } from "./DatastoreStagedResourceTreeAPIResponse";

export type CursorPage_DatastoreStagedResourceTreeAPIResponse_ = {
  items: Array<DatastoreStagedResourceTreeAPIResponse>;
  total: number;
  /**
   * Cursor to refetch the current page
   */
  current_page?: string | null;
  /**
   * Cursor to refetch the current page starting from the last item
   */
  current_page_backwards?: string | null;
  /**
   * Cursor for the previous page
   */
  previous_page?: string | null;
  /**
   * Cursor for the next page
   */
  next_page?: string | null;
};
