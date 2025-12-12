import { baseApi } from "~/features/common/api.slice";
import { Page_EventAuditResponse_ } from "~/types/api/models/Page_EventAuditResponse_";
import { TaxonomyCreate } from "~/types/api/models/TaxonomyCreate";
import { TaxonomyResponse } from "~/types/api/models/TaxonomyResponse";
import { TaxonomyUpdate } from "~/types/api/models/TaxonomyUpdate";

import { TaxonomyEntity } from "./types";

type TaxonomySummary = { fides_key: string; name: string };

const taxonomyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getTaxonomy: build.query<TaxonomyEntity[], string>({
      query: (taxonomyType) => ({ url: `taxonomies/${taxonomyType}/elements` }),
      providesTags: (result, error, taxonomyType) => [
        { type: "Taxonomy", id: taxonomyType },
      ],
      // Ensure parents are listed before children so the tree can link edges correctly
      transformResponse: (items: TaxonomyEntity[]) => {
        const result: TaxonomyEntity[] = [];
        const remaining = [...items];

        // Add all root items first (no parent)
        const rootItems = remaining.filter((i) => i.parent_key === null);
        rootItems.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
        result.push(...rootItems);

        // Work through children ensuring their parent already exists in result
        let pending = remaining.filter((i) => i.parent_key !== null);
        while (pending.length > 0) {
          const toAdd = pending.filter((i) =>
            result.some((r) => r.fides_key === i.parent_key),
          );

          if (toAdd.length === 0) {
            // Fallback: break potential cycles by appending remaining items alphabetically
            result.push(
              ...pending.sort((a, b) => a.fides_key.localeCompare(b.fides_key)),
            );
            break;
          }

          toAdd.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
          result.push(...toAdd);
          pending = pending.filter((i) => !toAdd.includes(i));
        }

        return result;
      },
    }),
    getCustomTaxonomies: build.query<TaxonomySummary[], void>({
      query: () => ({ url: `taxonomies` }),
      providesTags: () => [{ type: "Taxonomy" }],
    }),
    createTaxonomy: build.mutation<
      TaxonomyEntity,
      { taxonomyType: string } & Partial<TaxonomyEntity>
    >({
      query: ({ taxonomyType, ...body }) => ({
        url: `taxonomies/${taxonomyType}/elements`,
        method: "POST",
        body,
      }),
      invalidatesTags: (result, error, { taxonomyType }) => [
        { type: "Taxonomy", id: taxonomyType },
        { type: "Taxonomy History", id: taxonomyType },
      ],
    }),
    updateTaxonomy: build.mutation<
      TaxonomyEntity,
      { taxonomyType: string } & Partial<TaxonomyEntity> &
        Pick<TaxonomyEntity, "fides_key">
    >({
      query: ({ taxonomyType, ...body }) => ({
        url: `taxonomies/${taxonomyType}/elements/${body.fides_key}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (result, error, { taxonomyType }) => [
        { type: "Taxonomy", id: taxonomyType },
        { type: "Taxonomy History", id: taxonomyType },
      ],
    }),
    deleteTaxonomy: build.mutation<
      string,
      { taxonomyType: string; key: string }
    >({
      query: ({ taxonomyType, key }) => ({
        url: `taxonomies/${taxonomyType}/elements/${key}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, { taxonomyType }) => [
        { type: "Taxonomy", id: taxonomyType },
        { type: "Taxonomy History", id: taxonomyType },
      ],
    }),
    createCustomTaxonomy: build.mutation<TaxonomyResponse, TaxonomyCreate>({
      query: (body) => ({
        url: `taxonomies`,
        method: "POST",
        body,
      }),
      invalidatesTags: () => [{ type: "Taxonomy" }],
    }),
    updateCustomTaxonomy: build.mutation<
      TaxonomyResponse,
      TaxonomyUpdate & { fides_key: string }
    >({
      query: ({ fides_key, ...body }) => ({
        url: `taxonomies/${fides_key}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (result, error, { fides_key }) => [
        { type: "Taxonomy" },
        { type: "Taxonomy History", id: fides_key },
      ],
    }),
    deleteCustomTaxonomy: build.mutation<void, string>({
      query: (fides_key) => ({
        url: `taxonomies/${fides_key}`,
        method: "DELETE",
      }),
      invalidatesTags: () => [{ type: "Taxonomy" }],
    }),
    getTaxonomyHistory: build.query<
      Page_EventAuditResponse_,
      { fides_key: string; page?: number; size?: number }
    >({
      query: ({ fides_key, page, size }) => ({
        url: `taxonomies/${fides_key}/history`,
        params: {
          page,
          size,
        },
      }),
      providesTags: (result, error, { fides_key }) => [
        { type: "Taxonomy History", id: fides_key },
      ],
    }),
  }),
});

export const {
  useGetCustomTaxonomiesQuery,
  useGetTaxonomyQuery,
  useLazyGetTaxonomyQuery,
  useCreateTaxonomyMutation,
  useUpdateTaxonomyMutation,
  useDeleteTaxonomyMutation,
  useCreateCustomTaxonomyMutation,
  useUpdateCustomTaxonomyMutation,
  useDeleteCustomTaxonomyMutation,
  useGetTaxonomyHistoryQuery,
} = taxonomyApi;
