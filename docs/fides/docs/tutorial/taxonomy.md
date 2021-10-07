# Getting Acquainted with the Fides Taxonomy 
_In this section, we'll review what the Fides taxonomy is, how it was created, when and how it should be used._

The Fides taxonomy for data categories is a standard adapted from [ISO 19944](https://www.iso.org/standard/79573.html). This taxonomy provides descriptions of the types of sensitive, personally identifiable, or non-identifiable data that an organization could hold for any data subject. The hierarchical nature of the Fides taxonomy has a few notable benefits:

* Consistency: the taxonomy is used as a shared resource across your Fidesctl deployment(s). Because the taxonomy is derived from an international standard, it enables interoperability inside and outside of your organization. 
* Natural inheritance: the hierarchy allows ease of reference to multiple subcategories or uncertain categorizations, simply by using a more superior data category.  
* Extensibility: if the taxonomy is missing any data categories specific to your business, you can extend the taxonomy with whatever new values you need. 

The Fides Taxonomy is used across the Fides ecosystem of projects, fidesctl and fidesops. 

## Why did we create the Fides Taxonomy?
The Fides taxonomy was created because the industry is distinctly lacking a common definition of what Personal Data is, what identifiable data is, and how anonymized data has to be to be unidentifiable. The taxonomy provides this common classification and is a key component of implementing Privacy as Code. 

## How to use the Fides Taxonomy
The Fides project comes with 4 taxonomies by default:

* Data categories
* Data subjects
* Data uses
* Data qualifiers

You can find these in the folder `fides/fidesctl/default_taxonomy/`, where you can modify these taxonomies for your own business uses.
