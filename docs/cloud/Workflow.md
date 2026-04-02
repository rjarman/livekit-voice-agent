---
slug: /workflow
sidebar_position: 7
---

# Workflow 

## Overview

Blocks Workflow is a visual automation builder for connecting apps and orchestrating tasks. Design workflows with triggers, actions, and conditional paths using a drag-and-drop interface.

**Dynamic, Flexible, Little to No Code**

:::info
**Developer Preview Release**

Core functionality is available. Advanced features like conditionals, loops, and built-in functions are coming soon.
:::

---

## Core Concepts

### Nodes

Every step in a workflow is called a **node**. Each node is specialized for a specific type of task. You can add nodes, configure them, and connect them in a logical sequence to accomplish your desired outcomes.

### Trigger Nodes

**Triggers** are the initiation points of a workflow. A workflow executes only when the trigger's conditions are met. Every workflow must start with a trigger node.

**Available Triggers:**

- Webhook – Starts the workflow when the Execute button is clicked, making it ideal for quick tests and manual runs.
- Email Trigger – Automatically triggers workflows when an email is received, enabling teams to build email-driven automations and integrations.

### Action Nodes

**Action Nodes** perform tasks such as calling a service, fetching data, sending emails, or making HTTP requests.

**Available Actions:**

- AI Agent – Executes an AI-powered agent to perform reasoning, decision-making, or task automation within the workflow.
- Send Email – Sends an email as part of the workflow process.
- HTTP Request Sends HTTP requests as part of the workflow process and supports full configuration of:
  - Request headers
  - Query parameters
  - Request body

### Executions

Each run of a workflow is considered an **execution**:

- **Node Execution:** Running an individual node (typically during configuration and testing)
- **Workflow Execution:** Running the entire workflow from trigger to completion

Each workflow execution has its own unique history that can be viewed from the **Executions** tab.

### Execution Path

Workflows are executed starting from the trigger node and following connected paths:

- Each connected node is executed in the order of the connections
- Each node can access the data output from all nodes that executed before it in the chain
- Nodes execute sequentially following the connection flow

### Expressions

**Expressions** are used to reference data and variables within your workflow. They follow a specific syntax and are always wrapped in **double curly braces**: `{{}}`

Expressions allow you to:

- Reference output from previous nodes
- Pass dynamic data between nodes
- Configure node parameters with values from earlier steps

See the **Writing Expressions** section for detailed syntax.

---

## Available Nodes

### Webhook

Generates a unique HTTP webhook URL that can be called to execute the workflow.

**Configuration:**

- Automatically generates a unique URL upon workflow creation/activation
- Copy the webhook URL and use it in external systems

**Current Behavior:**

- The webhook must be called as an **HTTP POST** request
- The request body must contain a **RAW JSON** payload
- The webhook returns an **instant HTTP 200 response** with a message indicating the workflow has been queued
- The workflow executes asynchronously after the response is sent

**Output:**  
The webhook node outputs the entire JSON payload received in the POST request, which can be referenced by subsequent nodes.

**Current Constraints:**

- Only POST requests are supported
- Only RAW JSON request bodies are supported
- No support for GET requests, headers, query parameters, or other body formats

**Planned Features:**

- GET request support
- Custom headers in requests
- Query parameters
- Multiple body formats (form-data, x-www-form-urlencoded)
- "Respond to webhook" node to send custom responses
- "Respond after last node" option to return workflow results

---

### Blocks Email Trigger

Triggers the workflow when an email is received in a connected inbound mailbox through Blocks Email Service.

**How It Works:**

- Connects to your mailbox via IMAP
- Polls the mailbox at regular intervals (configurable)
- Triggers the workflow when a new email is detected

**Output Parameters:**

| Parameter | Description |
| --- | --- |
| `ItemId` | Unique identifier for the email item |
| `MessageId` | Email message ID from headers |
| `MailServerConfigurationId` | ID of the connected mailbox configuration |
| `Subject` | Email subject line |
| `From` | Sender email address |
| `To` | Recipient email address(es) |
| `Body` | Email body content |
| `Status` | Processing status of the email |
| `Error` | Error message if any occurred during retrieval |
| `Date` | Email date/timestamp |
| `RawMime` | Raw MIME content of the email |
| `IsInBound` | Boolean indicating if email is inbound (always true for this trigger) |

**Current Constraints:**

- Only mailboxes with IMAP support can be connected
- Uses polling mechanism (not real-time push)

**Example Usage:**  
Trigger workflows based on incoming support emails, form submissions, or automated notifications.

---

### AI Agent

Allows you to integrate Blocks AI Agents into your workflow. AI Agents are custom intelligent agents you build within the Blocks platform.

**How It Works:**

- Select a pre-configured AI Agent from your Blocks workspace
- Provide input to the agent (can be static text or dynamic data from previous nodes)
- The agent processes the input according to its configuration, which may include:
    - Knowledge retrieval from connected data sources
    - Tool calling and function execution
    - Natural language processing
    - Data analysis and transformation
- The agent's response becomes available as output for subsequent nodes

**Use Cases:**

- Analyze email content and extract key information
- Generate responses or summaries
- Make intelligent decisions based on workflow data
- Process natural language inputs
- Query knowledge bases or documents

**Example:**  
Use an AI Agent to analyze incoming support emails, categorize them, and extract customer intent before routing to the appropriate action.

---

### Send Email

Sends emails using the Blocks Email Service with pre-configured email templates.

**How It Works:**

- Email templates are created and managed separately in Blocks Template Management service
- Templates support dynamic variables (placeholders)
- In the workflow, you select which template to use
- You provide values for the template variables dynamically based on workflow logic

**Configuration:**

- **Template:** Select from your available email templates
- **Recipient:** Specify email address(es) - can be dynamic using expressions
- **Template Variables:** Map workflow data to template variables

**Example:**  
If your template has variables `{{customer_name}}` and `{{order_id}}`, you can populate these with data from previous workflow nodes like webhook input or AI Agent output.

**Current Constraints:**

- Templates must be created in Blocks Template Management service before use
- Template variable structure is defined in the template, not in the workflow

---

### HTTP Request

Make HTTP requests to external APIs and services from your workflow.

**Supported Methods:**

- GET
- POST
- PUT
- PATCH
- DELETE

**Supported Parameters:**

| Parameter Type | Description |
| --- | --- |
| **Query Params** | URL query parameters (e.g., `?key=value&foo=bar`) |
| **Headers** | Custom HTTP headers for authentication, content-type, etc. |
| **Body** | Request body in JSON format only (for POST, PUT, PATCH) |
| **Path Params** | Dynamic URL path segments using expressions directly in the URL field |

**Example URL with Expressions:**

```
https://api.example.com/users/{{$json.output.userId}}/orders
```

**Use Cases:**

- Call external APIs to fetch or send data
- Integrate with third-party services
- Post data to databases or analytics platforms
- Trigger actions in other systems

**Current Constraints:**

- Only JSON body format is supported
- No built-in OAuth or advanced authentication (use headers for API keys/tokens)

**Planned Features:**

- OAuth authentication support
- Multiple body formats (form-data, XML, etc.)
- Certificate-based authentication

---

## Writing Expressions

Expressions allow you to dynamically reference data from previous nodes in your workflow. They are wrapped in **double curly braces** `{{}}`.

### Syntax Rules

#### Referencing the Immediate Previous Node

When you want to reference output from the node directly connected before the current node:

```
{{$json.output.<param_name>}}
```

**Breakdown:**

- `$json` - Indicates we're accessing JSON data from the previous node
- `.output` - References the output section of that node
- `.<param_name>` - The specific parameter/key you want to access

**Examples:**

```
{{$json.output.email}}  
{{$json.output.Subject}}  
{{$json.output.userId}}
```

#### Referencing Any Previous Node (by Name)

When you want to reference output from a specific node that is not the immediate previous node:

```
{{$node["<​Node Name>"].json.output.<param_name>}}
```

**Breakdown:**

- `$node["<​Node Name>"]` - Targets a specific node by its name
- `.json` - References the JSON data from that node
- `.output` - References the output section
- `.<param_name>` - The specific parameter/key you want to access

**Examples:**

```
{{$node["Webhook"].json.output.customerEmail}}  
{{$node["Email Trigger"].json.output.Subject}}  
{{$node["AI Agent"].json.output.category}}
```

### Expression Examples

**Example 1: Using webhook data in an email**

```
Recipient: {{$node["Webhook"].json.output.email}}  
Template Variable (customer_name): {{$node["Webhook"].json.output.name}}
```

**Example 2: Using AI Agent output in HTTP request**

```
URL: https://api.crm.com/contacts/{{$json.output.contactId}}  
Body:   
{  
  "status": "{{$json.output.category}}",  
  "notes": "{{$json.output.summary}}"  
}
```

**Example 3: Passing email trigger data to AI Agent**

```
AI Agent Input: Analyze this email and categorize it: {{$json.output.Body}}
```

### Important Notes

- Node names must match exactly (case-sensitive)
- Parameter names must match the output structure of the node
- Use quotes around node names when using `$node["Name"]` syntax
- No built-in functions are currently available (string manipulation, date formatting, etc.) - coming in future releases

---

## Workflow Management

### Activation & Deactivation

- Workflows must be **activated** to run automatically when triggered
- **Deactivated** workflows will not execute, even if trigger conditions are met
- You can toggle activation status from the workflow settings
- Manual testing is available regardless of activation status

### Execution History

- Every workflow execution is logged with a complete history
- View execution details in the **Executions** tab
- See the data passed through each node
- Debug failures by examining node outputs
- **No current limits** on execution history retention

### Current Limitations

- No execution count limits per day/month
- No limits on number of nodes per workflow
- No automatic execution timeout (workflows run until completion)
- No workflow versioning (changes are applied directly)
- No rollback capability

**Planned Features:**

- Workflow versioning
- Execution limits based on plan tiers
- Configurable timeout settings
- Rollback to previous versions

---

## Upcoming Features

The following features are planned for future releases:

### Conditional Logic

- **IF/THEN nodes** for branching logic
- **Switch nodes** for multi-path routing
- Execute different paths based on conditions

### Loops & Iteration

- Loop over arrays of data
- Process multiple items sequentially or in parallel
- Batch operations

### Error Handling

- Try-catch mechanisms
- Fallback paths for failed nodes
- Retry logic with configurable attempts

### Data Transformation

- Dedicated nodes for data manipulation
- Filtering, mapping, and reducing arrays
- Date/time formatting
- String operations

### Built-in Expression Functions

- String manipulation (concatenate, split, replace, etc.)
- Mathematical operations
- Date/time functions
- Array operations (filter, map, find, etc.)
- JSON parsing and manipulation

### Additional Triggers

- **Schedule/Cron triggers** for time-based automation
- **Database triggers** for data changes
- **Form submission triggers**

### Enhanced HTTP Request

- OAuth 2.0 authentication
- Multiple body formats (form-data, XML, GraphQL)
- File upload support
- Certificate-based authentication

### Webhook Enhancements

- GET request support
- Custom response handling
- Synchronous execution with result response
- Header and query parameter support

---

## Support & Feedback

This is a Developer Preview release. Your feedback is invaluable for improving Blocks Workflow.

For questions, issues, or feature requests, please contact the Blocks platform support team.

---

**Last Updated:** Developer Preview Release
