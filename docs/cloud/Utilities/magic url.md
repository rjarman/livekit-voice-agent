---
sidebar_position: 3
---

import CopyPageButton from '@site/src/components/Copy';

# Magic Links

<CopyPageButton inidividual= {true}/>

## Overview

The Magic Links service in Blocks Cloud enables administrators to create secure, time-limited URLs with two distinct types. **Redirect magic links** generate shortened URLs that direct users to specified endpoints, perfect for streamlined user journeys. **Action magic links** execute predefined backend actions when accessed, enabling automated workflows and system events without user interaction. Both types support configurable usage limits and expiration dates, ensuring secure and controlled access within the Construct environment.

## Navigating to Magic Links

1. Navigate to **Utilities** → **Magic URL**. 
2. The Magic URL dashboard displays a table of all existing magic links and their configurations.
3. To create a new magic link, click the **Add Magic Link** button.
4. To manage or view details of an existing link, click on its row.

## Creating a Magic Link

All magic links require the following core configuration:

### URL *

The destination URL where users will be directed or where the action will be executed (e.g., `https://example.com`).

### Name *

An identifier for the magic link, typically an email address or username (e.g., `john.doe@yopmail.com`).

### Client Credential

Specify the client credential associated with the magic link. This determines which application or service can use the link and controls the authentication scope.

### Usage Limit (Optional)

Toggle to set the maximum number of times a magic link can be used. Once this limit is reached, the link becomes inactive. Leave disabled for unlimited usage.

### Auto Expiry Date (Optional)

Toggle to define when the magic link expires. After this date, the link will no longer function, ensuring time-limited security for sensitive operations.

:::note
Magic links need to be triggered from the code when designed for user flows. Ensure your application code includes the logic to generate and send magic links to users when needed.
:::

## Types of Magic Links

Magic links come in two types, each serving different use cases:

### Redirect

Redirect magic links create shortened URLs that redirect users to your configured destination while maintaining the authentication context.

**Configuration fields:**
- **URL:** The destination URL for redirection
- **Name:** Identifier for the magic link
- **Type:** Select "Redirect"
- **Client Credential:** Authentication scope
- **Set Usage Limit:** Optional toggle to limit link usage
- **Set Auto Expiry Date:** Optional toggle to set expiration

**Key features:**
- Creates shortened, shareable links
- Automatically redirects users to the specified endpoint
- Maintains authentication state throughout the redirect

### Action

Action magic links trigger predefined backend actions when accessed. Unlike redirect links, action links execute a specific HTTP request and return a response or status without redirecting the user. Use action links to automate backend workflows, confirm user actions, or trigger system events.

**Configuration fields:**
- **URL:** The API endpoint to call
- **Name:** Identifier for the magic link
- **Type:** Select "Action"
- **Request Method:** Choose between GET or POST
- **Request Payload:** JSON payload to send with the request (e.g., `{}`)
- **Request Headers:** Custom headers for the request (e.g., `{"Authorization": "Bearer..."}`)
- **Encoded Query String:** URL-encoded query parameters
- **Client Credential:** Authentication scope
- **Set Usage Limit:** Optional toggle to limit link usage
- **Set Auto Expiry Date:** Optional toggle to set expiration

**Key features:**
- Executes HTTP requests (GET or POST) to backend services
- Supports custom headers and payloads
- Returns response or status directly
- No automatic redirection
- Ideal for automated workflows and event triggers

## View and Manage Magic Links

1. Navigate to **Utilities** → **Magic URL**. The Magic URL dashboard displays all created magic links.
2. The table includes:
   - All custom magic links created by users
   - Configuration details and link type
3. Use the **search field** to find magic links by name or identifier.
4. Filter magic links using available filters to organize by type, credential, or status.
5. To edit a magic link, click on the desired row. This opens the Edit page where you can update configurations or view usage statistics.
6. To delete a magic link, click the three-dot menu beside the desired link and select **Delete**.

## Configuration

### Configure Your Base URL

To use magic links effectively, configure your custom short URL base:

1. Navigate to **Utilities** → **Magic URL**.
2. Click **Configure Magic URL** or access the settings panel.
3. Enter your **Context Name** (e.g., "Default", "Production").
4. Enter your **Short URL Base** (e.g., `https://dev-short.seliseblocks.com/`).
5. Click **Save**.

:::note
When you configure a custom base URL, proper redirect handling must be implemented on your server side to route incoming magic link requests to the appropriate endpoints.
:::

## Frequently Used Scenarios

**Passwordless Login:** Create redirect magic links that authenticate users without requiring passwords, perfect for seamless single-sign-on experiences.

**Email Verification:** Send action magic links in verification emails that confirm user email addresses when clicked.

**Password Reset:** Generate time-limited redirect magic links for secure password reset flows.

**User Invitations:** Create shareable redirect magic links for inviting team members or clients into your application.

:::tip
For multi-environment workflows, use different Context Names and base URLs for development, staging, and production environments to maintain clear separation and control.
:::

---

