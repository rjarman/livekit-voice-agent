---
slug: /models
sidebar_position: 3
---

import CopyPageButton from '@site/src/components/Copy';

# Models

## Overview

Blocks AI is built to be **Model Provider Agnostic**. Users can choose any model provider they prefer—whether from major official LLM providers or custom models hosted on their own infrastructure.

Under **AI > Models**, users can add their desired models and start using them with Blocks AI. For users who do not have access to AI models, Blocks Cloud offers the following preconfigured models from **Azure OpenAI**:
- GPT-5 Mini  
- GPT-4o  
- GPT-4o Mini  

---

## Setting Up Your Own Models

From the side navigation, go to **AI > Models**. There are two main sections:

### Official API
Quickly connect to supported LLM providers by simply adding your API key—no custom configuration required.

### Open Deployment
Open Deployment allows configuration and hosting on custom domains, offering more flexibility than official APIs. Users can also connect self-hosted models using the **Custom Model** configuration.

This option supports:
- Provider-specific deployments  
- Fully custom provider endpoints  
- Advanced configuration options  

Users can select providers from major vendors or integrate custom-hosted providers using built-in provider management tools.

![AI](/img/Models1.png "Models")

---

## Adding Official APIs

If you already have API keys from supported providers:

1. Select the provider you want to connect.
2. Open the provider’s details page.
3. Click **Add Model**.
4. On the **Add \<Provider Name> Model** screen:
   - Select the desired model from the dropdown
   - Paste your API key
   - Provide any additional provider-specific configuration
5. Click **Save**


![AI](/img/Models2.png "Models")

---

## Adding Open Deployments

Open Deployment supports the following options:

### Azure

Since Azure supports custom domains, it is configured under **Open Deployments**.

Steps:
1. Select **Azure**
2. Open the Azure models page
3. Click **Add Models**

Configuration fields:
- Select Model  
- Enter URL  
- Enter Deployment Name  
- Enter API Key  


![AI](/img/Models3.png "Models")

---

### OpenRouter

As OpenRouter provides a unified API to access multiple LLM providers, it is also configured under **Open Deployments**.

Steps:
1. Select **OpenRouter**
2. Open the OpenRouter models page
3. Click **Add Models**

Configuration fields:
- Select Model  
- Enter URL  
- Enter Deployment Name  
- Enter API Key  

![AI](/img/Models4.png "Models")

---

### Custom Models

For self-hosted models or providers not listed separately, use **Custom Models**.

Steps:
1. Click **Custom Models > Add Model**
2. In the configuration screen, enter:
   - Model Name  
   - Provider Name  
   - API URL  
   - API Key  
   - API Version  

3. Configure the following (or keep defaults):
   - Temperature  
   - Maximum Tokens  
   - Custom Headers and Keys (if required)

4. Click **Save Model**


![AI](/img/Models5.png "Models")

---

## Validating Added Models

Once added, models will appear in the model list under their respective provider configurations.

To validate connectivity:
- Click the **Validate** icon next to the model


![AI](/img/Models6.png "Models")

