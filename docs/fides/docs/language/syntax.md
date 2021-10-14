# Fides Configuration Syntax

Other pages in this language section describe various concepts and resources that appear in the Fides language. This page describes the syntax of the language in more detail to help better interpret Fides whether you're authoring or reading.

The Fides language is an intentionally simple language designed to be relatively easy for anyone to read and write. The primary objective is to translate complex privacy compliance concepts into a simple syntax, it's for this reason Fides is entirely written as YAML configurations.

## YAML - Building Block of Fides

### Fides Taxonomy

The Fides language is intentionally simple. To assure this, Fides declarations use predefined primitives (e.g. data categories) that are used when describing your datasets, systems, policies, etc. These predefined primitives exist as part of the Fides taxonomy which is maintained in your `fidesctl` server so they can be consistently used across your organization's development team. 

You can learn more about the taxonomy structure and how to extend it in the [taxonomy guide](taxonomy.md).

### Dot Notation and Snake_Case

To make writing and reading Fides language as easy for humans as possible, declarations from the privacy taxonomy use `dot notation` for the keys and use `snake_case` compound labels.

For example, to describe a field in a database as information provided by a user that is personally identifiable, you can write it's data category as:

``` yaml
# This declares that the data is provided by the user and identifies them directly
user.provided.identifiable
```

If we require greater specificity that just "identifiable", we could declare the contact type as a phone number by using a more specific sub-category:

``` yaml
# This declares that the is data provided by the user,
# identifies them directly and is from the contact category and of type phone number.
user.provided.identifiable.contact.phone_number
```

The diagram below shows you the structure of that statement:

![alt text](../img/notation-conventions.svg "Fides Manifest Workflow")

### Key-Value 

The key-value is YAML, and Fides', basic building block. Every item in a Fides YAML document is a member of at least one dictionary. The key is always a `string`. The value is a scalar so that it can be any datatype. So the value can be a `string`, a `number`, or another `dictionary` - most commonly in Fides, this will be a `string` that may provide a description or a pointer to a reference object in the taxonomy.

If we use the example of a user's contact email, to correctly declare this in valid Fides YAML as part of a Dataset, it would be:

``` yaml
  fields:                           # Group of fields in the dataset.
    - name: email
      description: User's Email
      data_categories:              # Data category label(s) to assign field.
        - user.provided.identifiable.contact.email
        - account.contact.email
```
The key for each key-value pair determines what value types are valid (for example, a resource type such as `data_categories` must use values from the Data Categories taxonomy), but many keys accept arbitrary strings as descriptive labels.

Finally, as you see in the example above, keys such as `data_categories` accept a list of values for multi-labeling. In this case, the field email has been assigned the value **user provided identifiable contact email** as well as **account related contact email**, indicating that it may be either of those categories when used.


## Character Encoding

Fides configuration files must always be UTF-8 encoded. While the delimiters of the language are all ASCII characters, Fides accepts non-ASCII characters in key-values, comments, and string values.