---
slug: /agents
sidebar_position: 1
---

import CopyPageButton from '@site/src/components/Copy';

# Agents

## Overview

**Agents** serve as the central hub for creating, configuring, and deploying AI agents across your platform. It enables teams to design intelligent assistants that can understand user context, access knowledge, and interact naturally — all without complex technical set up.

Each agent can have a unique personality, knowledge base, and behavior settings. Users can equip agents with custom data, adjust tone and formality, configure memory and retrieval settings, and integrate them seamlessly into web applications either via an embedded script or in a standalone immersive mode.

This document provides step-by-step guidance on:

- Creating agents using predefined templates or custom configurations
- Configuring LLM models and parameters
- Connecting up knowledge bases and performing retrieval testing
- Enabling tools, memory, welcome guides, and guardrails
- Customizing the chatbot's design and embedding it into applications
- Managing conversations, global settings, and publishing the agent

It is intended for both technical and non-technical users to efficiently deploy AI agents within the Blocks platform.

---

## Create an AI Agent

AI Agents can be created for different purposes, personas and with different capabilities and access to different sets of knowledge bases as per the use cases. Getting started with AI Agents is very easy in blocks.

![AI](/img/agent-create.png "Create Agent")

Steps:

- Go to AI -> Agents
- Click Add Agent

The agent creation screen will appear and will guide you based on your needs.

Agents are classified into two main types:

- Sequential
- Reasoning

:::info
Sequential agents plan all tasks together and executes them in parallel, while Reasoning agents perform tasks step-by-step; Reasoning agents perform better in complex scenarios but also consume more AI Credits.
:::

### Using Predefined Templates

The defult view for creating agent shows you the option to create agents from templates.

![AI](/img/agent-create-template.png "Create agent from template")

You can choose any of the default templates that align with your needs such as: Customer Service, IT Support, HR Assistant etc.”.

Choose an Agent Type "Sequential" or "Reasoning".

Click on “Create” button to complete the creation of your new agent and proceed with configuring it further.

### Creating a Custom Agent

You can also create an agent with custom informaiton.

Click on Create Custom Agent, then provide the following details:

![AI](/img/agent-create-custom.png "Create agent from template")

- Agent Name – Enter a name for your agent
- Description – Define the purpose and role of the AI agent
- Choose Agent Type "Sequential" or "Reasoning".

After entering the required information, click Create to complete the setup and proceed with further configuration.

---

## Configuring Your Agent

This section provides deep control over agent behavior and is especially useful for technical users with working knowledge of AI models. The following sections allow you to modify the agent’s behavior.

:::info
To configure, perform retrieval testing, manage integrations, or view conversations for a specific bot, select the agent. This will take you to the agent’s dedicated configuration page where all settings can be managed by following the steps below.
:::

![AI](/img/agent-config.png "Agent Configuration")

By clicking the Edit button next to the agent name, you can change the agent’s image, name, and description and type.

---

### LLM

#### Select Model

##### My Models

- Use your own configured models
- Configure them from the **Models** section
- Models appear under **My Models**

##### Blocks Models

Blocks uses Azure-hosted models, the models provided here are:

- GPT-5.2
- GPT-5
- GPT-4o
- GPT-4o Mini

Select a model from the dropdown.

#### Model Parameters

- **Temperature** – Controls creativity
  - Low = focused responses
  - High = more variation
- **Max Tokens** – Maximum response length
- **Base Prompt** – Base instruction for agent behavior

---

### Knowledge Base

:::info
Knowledge Base must be enabled and Folders must be added to the agent in order for RAG to take effect.
:::

From this section, you can enable or disable the knowledge base using the toggle.

Once enabled, use the "Add" button to add already created knowledge base folders to the agent. Multiple folders can be attached to an agent.

- You can also configure the following retrieval settings:

- Question Enhancements: Improves user questions automatically for better search results

- Knowledge Relevance: Controls how strictly the AI prioritizes your knowledge base when generating answers. Higher values enforce stricter matching.

- Recall Number: Sets how many knowledge chunks are retrieved per response

- Search Weight: Adjusts the balance between semantic search and keyword-based retrieval

---

### Tools

In Blocks, AI Tools allow an AI agent to call APIs to perform specific tasks by fetching or processing external data and using that data to generate accurate, context-aware responses.

From this screen, you can enable or disable the Tools section. To configure tools, navigate to the Tools section.

After configuring the tools, click Add, add a tool or MCP server, and click Save. The saved tools will then appear in this section.

---

### Memory

You can enable or disable conversations summaries and configure memory rounds.

- Summary: Enables conversation summarization for better context retention

- Rounds: Defines how many conversation rounds are retained as short-term memory (maximum 20)

---

### Welcome Guide

You can configure the greeting message for your agent here.

You may also enable or disable:

- Smart Suggestions
- Preset Questions
  1. Click **Add Question**
  2. Enter question
  3. Max **5 questions**
  4. Can be deleted anytime

---

### Human Handoff

This feature will be available in a future release.

---

### Guardrails

You can enable or disable guardrails using the toggle.

Guardrails are divided into multiple sections, each containing configurable items that can be enabled or disabled as needed.

#### Validation Stages

- User Query Validation: Applies checks before sending input to the LLM
- Agent Response Validation: Applies checks after the LLM generates a response

#### Safety Checks

- Personal Information Identification (PII): Detects and redacts personally identifiable information
- Injection Detection: Detects prompt injection attempts

#### Risk Thresholds

- Input Risk: Defines the risk level at which user input is flagged, modified, or blocked before reaching the LLM
- Output Risk: Defines the risk level at which the model’s response is filtered, modified, or blocked before being shown to the user

#### Blocked Content

- Keyword Checks - Enables banned keyword and pattern checks
  1. Sensitive Keywords: Words or phrases that trigger blocking or escalation
  2. Banned Patterns (Regex): Regular expressions used to block inputs or outputs
  3. Custom Rules - Up to five

---

## Playground

On the right side of the configuration page, a Playground is available to start conversations with the bot. This allows you to test behavior and changes without leaving the platform.

---

## Retrieval Testing

Retrieval Testing ensures the AI agent retrieves the most relevant knowledge by verifying accuracy and tuning relevance thresholds, recall numbers, and search weights before responding to user queries.

![AI](/img/agent-retrieval_testing.png "Agent Retrieval Testing")

To perform retrieval testing, go to the agent’s sidebar and open Retrieval Testing.

### Configure

- Enable Query Enhancement: Automatically improves user queries to increase retrieval accuracy.
- Relevance Score: Sets the minimum relevance threshold (0.70–0.95) required for knowledge chunks to be considered.
- Recall Number: Defines how many knowledge chunks are retrieved per query (10–20).
- Knowledge Retrieval Weight: Controls the balance between semantic and keyword-based search.
- Mixed Search: Combines semantic understanding and keyword matching for retrieval.
- Semantic Search: Prioritizes meaning-based retrieval over exact keyword matching.
- Re-rank Model: Re-ranks search results to improve relevance.
- Ground Truth Texts: Defines correct or expected results for retrieval testing.
  1. Enable this option using the toggle
  2. Enter the ground truth texts

---

### Query Field

This section allows you to check how closely the agent uses the stored knowledge.

Steps:

- Enter your question in the Query box
- Click Run
- The section below will display:
  1. Accuracy rate
  2. Retrieved knowledge chunks
  3. Detailed information about the sources used by the agent

---

## Integrations

After completing the setup of your agent, this section allows you to customize the look and feel of the chatbot and embed it into your site.

![AI](/img/Agents06.png "Agents")

---

### Design

This screen allows you to customize the appearance of your chat assistant. Any changes made in the right-hand panel are instantly reflected in the live preview on the left, enabling real-time design validation before saving.

#### Layout

- Left Side: Live preview of the chat widget
- Right Side: Configuration panel with styling and color options
- Save Button: Applies and stores all customization changes

#### Chat Header

Controls how the top bar of the chat widget appears.

- Start Color / End Color: Defines the gradient background for the chat header
- Title Color: Sets the color of the chat header title (e.g., “CareLink”)

#### Chat Style

Customizes the main chat area where messages appear.

- Background Color
- Font Color
- Button Color
- Icon Color
- Border Color

#### Toggle Button

Controls the appearance of the floating chat toggle button.

- Background Color
- Icon Color

#### Save Changes

Once satisfied with your customizations, click Save to apply the changes permanently. The chat widget will reflect the updated styles across your platform.

> **Tip**  
> You can automatically populate styling by providing a site link. The bot will crawl the site, learn its styling, and apply it to your agent widgets. Look for the Site URL field in the Design tab.

---

### Publish

#### Embed the script

In order to use the chatbot in your front-end app, go to the publish tab under the design section, copy the widget script, paste it in your front-end code.
The code will look like this:

```
<script
  src="https://gpt.seliseblocks.com/embed.js"
  data-widget-id="dc5***************************ae"
  data-widget-type="chat"
  data-project-key="18E***************************7C"
  data-app-domain="https://p******.seliseblocks.com"
  data-app-mode="dev">
</script>
```

Typically, you would paste the script at the bottom of your page right before the `</body>` tag

#### Standalone Mode

An immersive view of the chatbot. Copy and paste the link generted in the publish tab into a new tab or window or open it directly by clicking on the open button.

#### Scan the QR code

Scan the QR code and you will be taken to a immservive view of the chatbot.

---

### Global

Global settings are applied across the agent.

#### Banner

You can use an image or text as a banner for your chatbot.

- Add an image – Upload a visually appealing banner image (e.g., your logo or a welcoming graphic).
- Add text – Include a tagline or short greeting inside the banner.
- Enable/disable – Turn the banner on or off depending on your preference.

Once done, you can now see the banner in the chatbot. It looks nice when in full view.

#### Greetings

Set the greeting message for your chatbot here.

---

## Conversations

Go to the Conversations page from the agent’s sidebar. There, you can view a list of all past conversations.

### View response details

- Select a conversation. You will find a Details button next to each response.

- Click the Details button to open a new tab containing a detailed breakdown:

**Breakdown Details:**

**Overview:** Displays the model used, query type, response strategy, and processing time used to generate the response.

**Workflow Steps:** Shows the step-by-step workflow followed during response generation.

**Query:** Records the initial query sent to the LLM, along with any sub-queries generated.

**Tools:** Shows which tools were used, the input parameters passed, and the output generated. All tool inputs and outputs are displayed in JSON format.

**Sources:** Lists all sources used to generate the response.

![AI](/img/Agents08.png "Agents")

---

> **Note**  
> Agents can be deleted from this page using the Delete option in the three-dot menu
