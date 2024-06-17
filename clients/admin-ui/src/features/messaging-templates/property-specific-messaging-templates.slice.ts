import { baseApi } from "~/features/common/api.slice";

export type MinimalProperty = {
    id: string;
    name: string;
}

export type MessagingTemplateResponse = {
    type: string;
    id?: string; // not on default response
    is_enabled: boolean;
    content: {
        subject: string;
        body: string;
    };
    properties?: MinimalProperty[] // not on default response
};

export type MessagingTemplateDefaultResponse = {
    type: string;
    is_enabled: boolean;
    content: {
        subject: string;
        body: string;
    };
}

export type MessagingTemplateCreateOrUpdate = {
    is_enabled?: boolean
    content?: {
        subject: string;
        body: string;
    };
    properties?: MinimalProperty[]
};

export type MessagingTemplateUpdate = {
    templateId: string;
    template: MessagingTemplateCreateOrUpdate
}

export type MessagingTemplateCreate = {
    templateType: string;
    template: MessagingTemplateCreateOrUpdate
}



// Property-specific Messaging Templates API
const propertySpecificMessagingTemplatesApi = baseApi.injectEndpoints({
    endpoints: (build) => ({
        // Render data from existing template- GET by id
        getMessagingTemplateById: build.query<MessagingTemplateResponse, string>({
            query: (templateId: string) => ({
                url: `/messaging/templates/${templateId}`,
            }),
            providesTags: () => ["Property-Specific Messaging Templates"],
        }),
        // Update existing template
        updateMessagingTemplateById: build.mutation<
            MessagingTemplateResponse,
            MessagingTemplateUpdate
            >({
            query: ({templateId, template}) => ({
                url: `/messaging/templates/${templateId}`,
                method: "PUT",
                body: template,
            }),
            invalidatesTags: () => ["Property-Specific Messaging Templates"],
        }),
        // endpoint for rendering data for default template- GET by type
        getMessagingTemplateDefault: build.query<MessagingTemplateDefaultResponse, string>({
            query: (templateType: string) => ({
                url: `/messaging/templates/default/${templateType}`,
            }),
        }),
        // endpoint for creating new messaging template- POST by type
        createMessagingTemplateByType: build.mutation<
            MessagingTemplateResponse,
            MessagingTemplateCreate
            >({
            query: ({templateType, template}) => ({
                url: `/messaging/templates/${templateType}`,
                method: "POST",
                body: template,
            }),
            invalidatesTags: () => ["Property-Specific Messaging Templates"],
        }),
        // delete template by id
        deleteMessagingTemplateById: build.mutation<
            void,
            string
            >({
            query: (templateId: string) => ({
                url: `/messaging/templates/${templateId}`,
                method: "DELETE",
            }),
            invalidatesTags: () => ["Property-Specific Messaging Templates"],
        }),
    }),
});

export const {
    useGetMessagingTemplateByIdQuery,
    useUpdateMessagingTemplateByIdMutation,
    useGetMessagingTemplateDefaultQuery,
    useCreateMessagingTemplateByTypeMutation,
    useDeleteMessagingTemplateByIdMutation,
} = propertySpecificMessagingTemplatesApi;
