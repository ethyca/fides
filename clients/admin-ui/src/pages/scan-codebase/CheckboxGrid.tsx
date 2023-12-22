import React, { useState } from "react";

import { Formik, Form, FormikHelpers } from "formik";
import { Box, Button, Checkbox, VStack, Text, HStack } from "@fidesui/react";

interface CheckboxGridProps {
    options: string[];
}

const chunkArray = (arr: any[], size: number) => {
    const chunkedArray = [];
    for (let i = 0; i < arr.length; i += size) {
        chunkedArray.push(arr.slice(i, i + size));
    }
    return chunkedArray;
};

const CheckboxGrid: React.FC<CheckboxGridProps> = ({ options }) => {
    // Define the initial form values
    const initialValues = options.reduce((values, option) => {
        values[option] = false;
        return values;
    }, {} as Record<string, boolean>);
    const [selectedOptions, setSelectedOptions] = useState<string[]>([]);

    const handleFormSubmit = (
        values: Record<string, boolean>,
        { resetForm }: FormikHelpers<Record<string, boolean>>
    ) => {
        const selected = Object.keys(values).filter((option) => values[option]);
        setSelectedOptions(selected);
        resetForm();
    };

    const optionChunks = chunkArray(options, 3);

    return (
        <Box>
            <Formik initialValues={initialValues} onSubmit={handleFormSubmit}>
                <Form>
                    <VStack spacing={4}>
                        {optionChunks.map((row, rowIndex) => (
                            <HStack key={rowIndex} spacing={4}>
                                {row.map((option) => (
                                    <Checkbox key={option} name={option} colorScheme="purple"
                                    >
                                        {option}
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