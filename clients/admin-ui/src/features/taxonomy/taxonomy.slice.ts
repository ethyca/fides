import { baseApi } from "~/features/common/api.slice";

import { TaxonomyEntity } from "./types";

type TaxonomySummary = { fides_key: string; name: string };

const taxonomyApi = baseApi.injectEndpoints({
  endpoints: (build) => ({
    getCustomTaxonomies: build.query<TaxonomySummary[], void>({
      query: () => ({ url: `taxonomies` }),
    }),
    getTaxonomy: build.query<TaxonomyEntity[], string>({
      query: (taxonomyType) => ({ url: `taxonomies/${taxonomyType}` }),
      providesTags: (result, error, taxonomyType) => [
        { type: "Taxonomy", id: taxonomyType },
      ],
      // Ensure parents are listed before children so the tree can link edges correctly
      transformResponse: (items: TaxonomyEntity[]) => {
        const result: TaxonomyEntity[] = [];
        const remaining = [...items];

        // Add all root items first (no parent)
        const rootItems = remaining.filter((i) => i.parent_key == null);
        rootItems.sort((a, b) => a.fides_key.localeCompare(b.fides_key));
        result.push(...rootItems);

        // Work through children ensuring their parent already exists in result
        let pending = remaining.filter((i) => i.parent_key != null);
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
    createTaxonomy: build.mutation<
      TaxonomyEntity,
      { taxonomyType: string } & Partial<TaxonomyEntity>
    >({
      query: ({ taxonomyType, ...body }) => ({
        url: `taxonomies/${taxonomyType}`,
        method: "POST",
        body,
      }),
      invalidatesTags: (result, error, { taxonomyType }) => [
        { type: "Taxonomy", id: taxonomyType },
      ],
    }),
    updateTaxonomy: build.mutation<
      TaxonomyEntity,
      { taxonomyType: string } & Partial<TaxonomyEntity> &
        Pick<TaxonomyEntity, "fides_key">
    >({
      query: ({ taxonomyType, ...body }) => ({
        url: `taxonomies/${taxonomyType}`,
        method: "PUT",
        body,
      }),
      invalidatesTags: (result, error, { taxonomyType }) => [
        { type: "Taxonomy", id: taxonomyType },
      ],
    }),
    deleteTaxonomy: build.mutation<
      string,
      { taxonomyType: string; key: string }
    >({
      query: ({ taxonomyType, key }) => ({
        url: `taxonomies/${taxonomyType}/${key}`,
        method: "DELETE",
      }),
      invalidatesTags: (result, error, { taxonomyType }) => [
        { type: "Taxonomy", id: taxonomyType },
      ],
    }),
  }),
});

export const {
  useGetCustomTaxonomiesQuery,
  useLazyGetTaxonomyQuery,
  useCreateTaxonomyMutation,
  useUpdateTaxonomyMutation,
  useDeleteTaxonomyMutation,
} = taxonomyApi;
