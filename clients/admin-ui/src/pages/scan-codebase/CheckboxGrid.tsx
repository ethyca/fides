import React, { useState } from "react";

import { Formik, Form, FormikHelpers } from "formik";
import { Box, Button, Checkbox, VStack, Text, HStack } from "@fidesui/react";
const tags = [
    "Name",
    "Email",
    "Phone number",
    "Driver's license number",
    "Payment information",
    "Shipping information",
    "Date of birth",
    "Healthcare or medical information",
    "IP address",
    "Usernames and passwords",
    "Race or ethnicity",
    "Religious beliefs"
];

// Define the initial form values
const initialValues = tags.reduce((values, tag) => {
    values[tag] = false;
    return values;
}, {} as Record<string, boolean>);

const chunkArray = (arr: any[], size: number) => {
    const chunkedArray = [];
    for (let i = 0; i < arr.length; i += size) {
        chunkedArray.push(arr.slice(i, i + size));
    }
    return chunkedArray;
};

const CheckboxGrid: React.FC = () => {
    const [selectedTags, setSelectedTags] = useState<string[]>([]);

    const handleFormSubmit = (
        values: Record<string, boolean>,
        { resetForm }: FormikHelpers<Record<string, boolean>>
    ) => {
        const selected = Object.keys(values).filter((tag) => values[tag]);
        setSelectedTags(selected);
        resetForm();
    };

    const tagChunks = chunkArray(tags, 3);

    return (
        <Box>
            <Formik initialValues={initialValues} onSubmit={handleFormSubmit}>
                <Form>
                    <VStack spacing={4}>
                        {tagChunks.map((row, rowIndex) => (
                            <HStack key={rowIndex} spacing={4}>
                                {row.map((tag) => (
                                    <Checkbox key={tag} name={tag} colorScheme="purple"
                                    >
                                        {tag}
                                    </Checkbox>
                                ))}
                            </HStack>
                        ))}
                        <Button
                            textAlign="right"
                            type="submit"
                            colorScheme="primary"
                            size="sm"
                        >
                            Save
                        </Button>
                    </VStack>
                </Form>
            </Formik>
        </Box>
    );
};

export default CheckboxGrid;