---
sidebar_position: 2
---
import CopyPageButton from '@site/src/components/Copy';

# OIDC (OpenID Connect)

<CopyPageButton inidividual= {true}/>

## Overview

The OIDC (OpenID Connect) feature in the Blocks Cloud Platform enables applications to authenticate users using Blocks as a centralized Identity Provider (IdP).

It works similarly to logging into an application using Google or Microsoft SSO — instead of managing authentication internally, the application delegates authentication to Blocks. Blocks verifies the user and securely returns authentication information to the client application.

This allows organizations to:
- Centralize authentication across multiple applications
- Improve security by reducing duplicate login systems
- Provide a seamless SSO experience across services
- Integrate third-party and Construct applications with a single identity source

## How OIDC Works

The authentication flow follows the standard Authorization Code flow:

1. User clicks Login with Blocks
2. Application redirects the user to the Blocks login screen
3. User authenticates using Blocks credentials
4. Blocks sends an authorization code to the application's redirect URL
5. Application exchanges the code for tokens using Blocks OIDC endpoints
6. User is logged into the application

## Configuring OIDC

### Prerequisites

Before configuring OIDC, ensure the following are enabled:
- SSO must be enabled
- Authorization Code grant type must be enabled

⚠️ **OIDC will not work without the Authorization Code grant type enabled.**

### Creating an OIDC Client

**Steps**

1. Go to Core Services → Authentication
2. Navigate to the OIDC section
3. Click Create
4. Enter the following details:

| Field | Description |
|-------|-------------|
| Client Name | Name of the application using OIDC |
| Redirect URL | Callback URL where the authentication response will be sent |
| Audience | Base URL of the redirect URL |
| Branding Image | Logo displayed on the login screen |
| Theme Color | Primary UI color for the login screen |
| Scope | Fixed as openid |

5. Click Save

### Generated Credentials

After saving the OIDC client, the system generates the following:
- Client ID
- Client Secret
- Well-Known URL

📌 **These credentials must be securely stored and used in your application configuration.**

### Required Authentication Settings

Ensure the following grant types are enabled in Authentication → General → Grant Types:
- Authorization Code
- Email/Password (recommended as fallback)

## Use Cases

OIDC is designed primarily for external or third-party applications that need to authenticate users via Blocks without managing credentials internally.

### 1. Third-Party SaaS Authentication

Allow users to log into external applications using their Blocks identity. Instead of building a separate login system, the third-party app delegates authentication to Blocks.

**Example:** A web application such as smartblog.com integrates Blocks OIDC. Users click Login with Blocks, authenticate, and are redirected back as logged-in users — without the app ever handling credentials directly.

### 2. Multi-Application Ecosystem

Multiple applications across an organization share the same centralized login system using Blocks as the single identity provider.

### 3. Enterprise Identity Integration

Blocks acts as a central identity layer for all company applications, reducing the complexity of managing separate authentication systems per product.

### 4. Secure External Integrations

Partners and clients can authenticate securely using Blocks OIDC without requiring direct access to internal systems.

## Branding & Login Experience

OIDC allows customization of the login screen displayed to users during authentication:
- Upload your application logo (light mode and dark mode images supported)
- Set a primary theme color
- The login page will reflect your application branding instead of a generic UI

## Important Notes

| Requirement | Details |
|-------------|---------|
| Authorization Code Flow | Mandatory. OIDC will not function without it. |
| Scope | Always set to openid. This is fixed and cannot be changed. |
| Client Credentials | Must be securely stored after generation. |
| Redirect URL | Must exactly match the URL configured in the OIDC client. |
| Audience | Should match the base URL of the redirect URL. |
| SSO | Must be enabled in Blocks before configuring OIDC. |

## Implementing OIDC in Construct

### Overview

This section explains how to use OIDC specifically within Construct applications. Since Blocks is not listed as a default identity provider in Construct, OIDC integration requires using the Bring Your Own SSO option.

**Important Concept:** Construct does not list Blocks as a default identity provider. You must configure Blocks OIDC through Bring Your Own SSO.

### Steps to Implement OIDC in Construct

#### Step 1: Enable SSO in Construct

1. Open your Construct project
2. Go to SSO Settings
3. Enable SSO

#### Step 2: Enable "Bring Your Own SSO"

1. Navigate to SSO configuration
2. Select Bring Your Own SSO

This allows you to plug in Blocks as an external identity provider.

#### Step 3: Configure OIDC Credentials

From your OIDC client configuration, copy and enter the following:

| Field | Source |
|-------|--------|
| Client ID | From OIDC client configuration |
| Client Secret | From OIDC client configuration |
| Redirect URL | Same redirect URL as configured in OIDC |
| Well-Known URL | From OIDC client configuration |

Click Save to apply the settings.

#### Step 4: Enable Required Grant Types

Ensure the following grant types are enabled in Construct:
- Authorization Code
- Email/Password

⚠️ **If these grant types are not enabled, login will fail.**

#### Step 5: Environment Configuration

When running Construct locally or in a staging environment:
- Use the Stage Construct Repository (OIDC is supported in this version)
- Configure the following values:
  - Base URL
  - X-Blocks-Key
  - OIDC Client ID

**Note:** Production Construct may not yet fully support OIDC. Use the stage version for testing and development.

### User Login Experience in Construct

Once configured, the end-to-end login experience is as follows:

1. User opens the Construct application
2. Clicks SSO Login
3. Sees the Blocks Login Screen
4. Authenticates with Blocks credentials
5. Redirected back to Construct as an authenticated user

### Additional Notes for Construct

| Note | Details |
|------|---------|
| Email/Password Grant Type | Must be enabled or login may fail even with OIDC configured correctly. |
| Dark Mode Branding | Requires a separate dark mode branding image to display correctly. |
| Captcha | Can be removed if not required in your environment. |
| OIDC Support | Only the Stage version of Construct currently supports OIDC fully. |
