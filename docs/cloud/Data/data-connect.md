---
slug: /data-gateway
sidebar_position: 1
---

import CopyPageButton from '@site/src/components/Copy';

# Data Gateway

## Overview

The Data Gateway in Blocks Cloud provides a unified interface for managing, modeling, and accessing your application data. Users can define and customize schemas to structure their data, perform CRUD operations using the Data Playground, and manage access at both the schema and column levels with detailed security controls. Column-level validation ensures data integrity, while changes only take effect in the API after being published. This system enables users to efficiently organize, secure, and interact with their data in a controlled and customizable environment.

## Configuring a Data Source

Users can use Blocks Cloud's data which will be hosted on Block Cloud's infrastructure. Or you can choose to bring your own data for example, if you have data in MongoDBAtlas or other similar data hosting services.

### Use Blocks Cloud's Data

To use Blocks Cloud's data, click the "Configure" button. Select the "Blocks Database" option.

![Configure](/img/data1.png "Data Gateway")

### Set up your own data source

If the user wishes to use their own data source then they must specify the connection URL and the name of the database.

:::note
After configuring the database, you must activate the Data Gateway server. Click the Start button to activate the server. You may find that if you haven’t used the Data Gateway for a while, then your system will become inactive.
:::

## Creating a Schema

Users can define their own schema. In order to add a schema, click on the Add button in the "Schemas" section. Select "Entity" when the schema defines a table or a collection in the database. Select "Child" to create a nested object.

:::note
Changes made in the app will not be impacted until the reload button is pressed in the Schemas section
:::

## Editing a Schema

:::info
Newly created schemas will have some default properties. Users can choose to delete them.
:::

In order to edit a schema click on the "Edit" button in the Schema Structure section. Users will be able to add properties, delete properties, rename properties, change the data type, declare whether properties are arrays or not, and change the access level for each property.

### Editing Properties

Users can edit multiple properties at once by selecting multiple properties by clicking on the checkbox on the left of each property.

### Deleting Properties

To delete a property, click on "Edit" in the Schema Structure section. Select the property/properties you want to delete by click on the corresponding checkboxes on the left. Click on Action, then click on delete.

![Configure](/img/data2.png "Data Gateway Image changed")

:::note
Any changes made in the schema will not reflect in the API calls until "Reload" is pressed.
:::

## Consuming the data

Once the schemas have been provided, users would be able to do CRUD operations using GraphQL endpoints. In order to know what endpoint to use to interact with the data, click on the "Preview" button.

### Data Playground

Once schemas are configured, users can perform CRUD (Create, Read, Update, Delete) operations through the Data Playground.

To access it, click on the Playground button. The Playground provides predefined query snippets that help users quickly generate structured queries and reduce manual errors.

**Key Features:**

- Provides query suggestions based on the schema structure to help users build queries faster.
- Allows users to erase or clear data created within the playground.
- Enables separate execution of individual queries for better control and testing.
- Each query generated in the Preview section includes a “Try in Playground” button, which automatically prepopulates the Playground with that query in the correct context.

![Configure](/img/Data3.png "Data Gateway")

## Authorization

Blocks Cloud offers Row-Level Security (RLS) and Column-Level Security (CLS) for the schemas you create.

### Schema-Level Access Control

To configure Row-Level Security (RLS), go to the Basic Information section and click Schema Access. Schema-level access control determines who can View, Create, Edit, or Delete data within the schema. The current access configuration can be reviewed from the Main tab.

You will see four permission tabs: **View, Create, Edit, Delete**.

There are three types of access control:

- All Logged In – Accessible to all authenticated users from this collection with no restrictions. In order to see how to authenticate user, follow this [guide](https://docs.seliseblocks.com/reference/category/authentication-3).
- Public – Accessible without authentication
- Custom – Define custom access rules as per requirements

You can configure each permission type according to your needs.

![Configure](/img/Data4.png "Data Gateway")

### Column-Level Access Control

To configure Column-Level Security, click Edit in the Schema Structure and then click the Access button of a property. Users can also modify column-level access by clicking the user icon in the Access column. This will display three permission tabs: View, Create, and Edit.

There are four types of access control:

- Inherited – Follows the access policy defined at the schema level and does not have a separate policy of its own.
- All Logged In – Accessible to all authenticated users from this collection with no restrictions. In order to see how to authenticate user, follow this [guide](https://docs.seliseblocks.com/reference/category/authentication-3).
- Public – Accessible without authentication
- Custom – Define custom access rules as per requirements

You can configure column access according to your requirements.

![Configure](/img/Data5.png "Data Gateway")

#### Custom access control

Custom Permissions allows you to define different types of rules for any permissions tab. To configure, select Custom as the access control for the desired tab, click the Add button, and provide a rule set name.

When creating rules, you can choose how multiple rules are applied:

- All of the following rules match – Every rule must be satisfied
- Any of the following rules match – At least one rule must be satisfied

![Configure](/img/Data6.png "Data Gateway")

**Rule Configuration**

For each rule, there are five dropdowns/options

1. **Source**

- Auth – Use user authentication data
- Schema Field – Use a field from the schema

2. Field

- For Auth: Select which authentication field to compare:
- UserID – Matches the logged-in user's ID
- Email – Matches the logged-in user's email
- Roles – Matches the roles assigned to the user
- Permissions – Matches user permissions
- For Schema Field: Select the schema field to compare (e.g., isDeleted, itemId)

3. Operator

Choose the comparison operator: **equal, not equal, in, not in, starts with, ends with, is null, is not null**

4. Compare With

- Auth – Compare with an authentication field
- Schema Field – Compare with another schema field
- Static – Compare with a fixed value

5. Field Selection (Depends on Compare With)

- Auth: Select field (UserID, Email, Roles, Permissions)
- Schema Field: Select field (isDeleted, itemId, etc.)
- Static: Enter the value manually

After configuring all options, click Save to apply the rule. Once saved, these rules enforce fine-grained access control based on your custom conditions.

#### Column-Level Validation

Column-level validation ensures that data entered into a property meets specific rules. In the Schema Structure section, click the icon under the Validation column for a property and then click Add Validation to set up validation for that column.

You will see the following fields:

- Regex Pattern
- Error Message

**How It Works:**

- Users can add a regular expression (regex) for a column.
- Every input value must match the regex pattern.
- If validation fails, the configured error message will be displayed.
- Only one regex expression can be added per column.
- The validation rule can be set to Active or Inactive.

![Configure](/img/Data7.png "Data Gateway")

#### Data Visualization

Data Visualization explains how to view and interact with data in your schema, including different formats, filters, and sorting options.

**Viewing Data**

Once you have inserted new data into your schema, you can visualize it by following these steps:

- Select a Schema:
- Navigate to the schema you want to view.
- By default, the Attributes tab will be selected.
- Switch to the Data Tab:
- Click on the Data tab next to the Attributes tab.
- Here, you will see a list of inserted or updated data entries.
- Available Formats: You can view your data in three different formats:
- Table View: Displays data in a structured table format. You can copy individual entry from here
- JSON View: Displays data in JSON format. You can copy the json code from here
- Data Details Section: Shows detailed information for each record individually. You can copy all the details of each record using the copy button

**Filtering Data**

The data view provides three types of filters to narrow down the results.

- Filter by Condition:
- Select one condition to filter the data. If you add another condition, you will see AND and OR operations.
- If you want to filter the data using all conditions, select the AND operation.
- If you want to filter the data using any one of the conditions, select the OR operation
- This allows you to view only the data that meets your specified criteria.

- Filter by Column:
- Choose single or multiple columns to display.
- This helps focus on the most relevant fields.

- Sort Data:
- Select any field to sort the data in ascending or descending order.
- This makes it easy to organize data based on your needs.

Among the three filters, regardless of which field you use in the view, each individual data entry in every column has a copy button beside it so that you can easily copy the value.

![Configure](/img/Data8.png "Data Gateway")

:::note
To migrate from one environment to the other, please follow [Environment Migration](https://docs.seliseblocks.com/cloud/getting-started#environment-selection).
:::
