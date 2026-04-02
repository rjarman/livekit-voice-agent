---
slug: /tools
sidebar_position: 2
---

import CopyPageButton from '@site/src/components/Copy';

# Tools

## Overview 

Modern AI needs to interact with the world beyond their training data – accessing real-time data, performing actions on behalf of the users in external systems, and integrating business workflows. This is what makes AI Agentic.  

Selise Blocks developed the Tools & MCP feature to simplify connecting agents to applications and systems. Enabling agents to graduate from RAG-powered chatbots to intelligent systems that can perform real tasks. 

This document outlines: 

- Tools Feature Overview 
- Necessity of MCP 
- Configuration of Tools & MCP in Blocks Cloud 

### Tools Feature 

The tools feature in Blocks Cloud is designed in a way that any external API can be mapped and made available to Blocks AI agents as tools. This allows for rapid integration of existing applications into Blocks Agents without having to build the MCP support on the end-application. 

AI systems often need to interact with external services to fetch data or perform actions. In Blocks, this is enabled through AI Tools and MCP Servers, which allow AI agents to safely and reliably work with external APIs. 

### MCP Feature 

MCP (Model Context Protocol) is the industry standard of exposing a set of tools to LLMs. Blocks also supports connecting to different MCP servers with various authentication methods for a seamless integration. 

---

## Adding a Tool 

You can define how a tool will assist your agent in performing tasks. 
 
Steps: 

- Go to AI > Tools 
- Click Add Tool 
- In the window:
  1. Enter the Tool Name
  2. Enter the Base URL
  3. Enter a description of how this tool should be used by the AI in conversations
  4. Click Create 

The tool will be added to the Tools tab. 

![AI](/img/Tools1.png "Tools")

> [!NOTE]
> **You can add a maximum of 5 tools and 5 MCP servers.

---

### Configuration

When you open a tool, you will see multiple tabs for different configuration sections. 

---

#### Authentication 

Authentication depends on the Base URL provider and the method they use. 

![AI](/img/Tools2.png "Tools")

**None:** 

- Optionally, use Headers (key & value)
- Save 

Note: 
Headers are used so the platform can return relevant information about the tool requester. This helps tool developers analyze tool usage data. You can add multiple headers by clicking the Add button. 

**Bearer:**  

In the Provide Authentication section: 
- Enter Key
- Enter Prefix
- Enter Secret
- Optionally, use Headers (key & value)
- Click Save.

**Basic:**  

In the Provide Authentication section: 
- Enter Key
- Enter Prefix
- Enter Username
- Enter Password
- Optionally, use Headers (key & value)
- Click Save. 

**API Token:**  

In the Provide Authentication section: 

Option 1: Location – Header 
- Select Location: Header
- Enter Key
- Enter Prefix
- Enter Secret
- Optionally, use Headers (key & value)
- Click Save. 

Option 2: Location – Query 
- Select Location: Query
- Enter Key
- Enter Secret
- Optionally, use Headers (key & value)
- Click Save. 

**OAuth2 Authentication:**

In the Configuration section: 

- Enter Client ID
- Enter Client Secret
- Enter Token URL
- Select Grant Type
- Enter Scopes (comma-separated)
- Optionally, use Headers (key & value)
- Click Save.

---

#### API  

From the API tab, you can create APIs for fetching data. You need to click on the Create API button 

**Basic Information** 

- Enter basic information:
  1. Name
  2. Description
  3. Provide Path: You can select any HTTP method – GET, POST, PUT, DELETE, PATCH
  4. Enter the Endpoint (e.g., POST – create agents)
- Click Continue.

![AI](/img/Tools3.png "Tools")

**Input Parameters**

You will be taken to the Input Parameters section. If you need to pass any parameters, add them here. 

- For each parameter:
  1. Enter Name (e.g., agentName)
  2. Enter Description (e.g., this is to collect the name of the agent)
  3. Select Type (e.g., String)
  4. Select Location (where you want to apply the parameter, e.g., Header)
  5. Enter Default Value (e.g., Battle Bot)
  6. Enable Required if you want to make this parameter mandatory 
- Use the Add button to add parameters. 
- Use the Delete button to remove a specific parameter. 
- Click Continue. 

![AI](/img/Tools4.png "Tools")

**Output Parameters**

You will be taken to the Output Parameters section. If you need to fetch or return any parameters, add them here. 

- For each parameter:
  1. Enter Name (e.g., agentId)
  2. Enter Description (e.g., this is to get the agent ID)
  3. Select Type (e.g., String)
  4. Select Location (where you want to apply the parameter, e.g., Body)
  5. Enter Default Value (e.g., AG123)
  6. Enable Required if you want to make this parameter mandatory in the output 
- Use the Add button to add parameters. 
- Use the Delete button to remove a specific parameter. 
- Click Save and Debug. 

![AI](/img/Tools5.png "Tools")

**Debugging** 

You will be taken to the Debugging tab. 

From here, you can: 

- Test your API with sample requests
- Validate inputs, outputs, and logic 

Steps: 

- Click Run Debug
- View the response in the right-side panel
- Click Complete to return to the API tab, where all configured APIs are listed 

You can also edit Swagger from this interface. 

![AI](/img/Tools6.png "Tools")

---

#### Tutorial Guide

You can edit and save the tutorial guide from the next tab.

![AI](/img/Tools8.png "Tools")

---

#### Dashboard

Dashboard is coming soon.

---

## Adding MCP Server 

You can use an MCP server as an AI tool to fetch information by exposing it as a callable, structured API. 

Steps: 

- Go to MCP Server
- Click Add MCP
- Enter the Tool Name and Description
- Click Save 

The MCP server will be added to the MCP server list. 

![AI](/img/Tools10.png "Tools")

---

### Configuration

- Open one of the MCP servers
- Click Config Params
- Select SSE or Streamable HTTP
- Enter the URL
- Select the Authentication Method 


![AI](/img/Tools12.png "Tools")

--- 

#### Authentication 

**None:** 

In the Provide Authentication section: 

- Enter Header key & value, or
- Enter Query parameters (key & value), or
- Use both
- Click Terms and Conditions,
- Click Save. 

**Bearer:** 

In the Provide Authentication section: 

- Enter Key
- Enter Prefix
- Enter Secret
- Optionally, enter Header key & value or Query parameters
- Click Terms and Conditions
- Click Save. 

**Basic:** 

In the Provide Authentication section: 

- Enter Key
- Enter Prefix
- Enter Username
- Enter Password
- Optionally, enter Header key & value or Query parameters 
- Click Terms and Conditions
- Click Save.

**API Token:** 

In the Provide Authentication section: 

- Select Header or Query
- Enter Key
- Enter Prefix
- Enter Secret
- Optionally, enter Header key & value or Query parameters 
- Click Terms and Conditions
- Click Save.
Click Terms and Conditions, then click Save. 

---
#### API Listing & Updates 

After configuration: 

- All available APIs from the MCP server will be displayed in a table format
- Click View to see API details, including input and output parameters
- Click Update API to fetch the latest MCP server data
 
![AI](/img/Tools13.png "Tools")

To use a specific tool or MCP server, you need to integrate it with an Agent. Please visit Tools section inside the Agent configuration. 
