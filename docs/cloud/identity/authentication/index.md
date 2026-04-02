---
sidebar_position: 1
---
import CopyPageButton from '@site/src/components/Copy';

# Authentication  

<CopyPageButton inidividual= {true}/>

## Overview

The Authentication service in the Blocks Cloud Platform provides a centralized and secure way to manage how users access Construct applications. It allows teams to configure authentication rules, choose supported login methods, and integrate external identity systems — all from a unified interface. With flexible options such as email/password login, social sign-in, client credentials, and external IdPs, the service ensures that each application can adopt the right level of security based on its requirements.
This module is organized into four key sections—General, Client Credentials, SSO, and External IdP — each designed to simplify configuration while maintaining strong security controls. From managing token lifecycles and account lockout policies to setting up OAuth providers and integrating identity systems like Keycloak, Okta, and Azure, the Authentication service equips teams with everything they need to implement reliable, scalable, and modern authentication across their Construct projects.

## Configuring General Authentication Settings  

The General section provides two key areas for setting up authentication in a Construct 
app:  
- Settings  
- Grant Types  

### Settings  

The Settings tab of General section defines the rules for user authentication.
![Authentication](/img/Authentication1.png "Settings")
    

| Option                          | Description                                                                               |
|---------------------------------|-------------------------------------------------------------------------------------------|
| Access Token Validity           | Sets how long an access token remains valid.                                              |
| Refresh Token Validity          | Determines the validity period for refresh tokens.                                        |
| 'Remember Me' Token Validity    | Controls session duration when the "Remember Me" option is enabled.                       |
|  Max Wrong Attempts Before Lock | Defines the number of failed login attempts allowed before an account is locked.          |
| Account Lock Duration           | Specifies how long an account remains locked after exceeding the allowed failed attempts. |


**Steps to Configure Settings**
1. Go to Core Services → Authentication . 
2. On the landing page, the General  tab will be open by default.  
3. Click the Edit  icon in the Settings  table.  
4. A pop-up window will appear.  
5. Enter your preferred values for each field.  
6. Click Save  to apply the changes.  

### Grant Types  
The Grant Types  tab allows users to choose which authentication methods will be 
available in the Construct app.  
 
   
 Available options include:  
- Email/Password  
- Social Login  
- Client Credentials  

Steps to Configure Grant Types  
1. On the General  tab (visible on the Authentication landing page), locate the Grant 
Type  table.  
2. Use the checkbox  to select one or multiple options.  
3. Click Save  to confirm your selections.  


:::note  
To enable Single Sign-On (SSO)  and Client Credentials, you must complete the 
configuration in the SSO and Client Credentials sections.  
:::
 
## Configuring Client Credentials Settings  
![Authentication](/img/Authentication2.png "Client Credentials")
 
Steps  
1. On the  Client Credentials tab.  
2. Click Create to generate a new client.  
3. Enter the required details:     
    a. Client Name  
    b. Roles  
4. Click Save to create the client.  
View the generated Client Secret and copy it for use in your application.  


## Configuring SSO Settings  

The Social section allows you to enable Single Sign -On (SSO)  using popular identity 
providers.  
Supported Providers:  
- Google  
- Microsoft  
- Others (coming soon)  

Steps to Configure SSO  
![Authentication](/img/Authentication3.png "SSO")
 
1. Go to Core Services → Authentication . 
2. On the landing page, open the SSO  tab.  
3. Locate your desired SSO provider and click the three-dot menu → Configure . 
4. A configuration page will appear asking for necessary details.  
5. Register your application with the selected SSO provider to obtain the following 
credentials:  
    a. Client ID  
    b. Client Secret  
    c. Redirect URL  
    d. Audience  
    e. Add other necessary  fields.( use setup guide for better understanding)  
6. Enter these details into the configuration form.  
7. Click Save  to apply the settings.  
Optional: Set Roles and Permissions  
 You can restrict SSO access based on user roles.  
 → Example: Only users with the admin  role can log in using Google SSO.  
 
## Configuring External IdP Settings  
Configure an External Identity Provider (IdP) to allow users to log in using accounts from trusted systems such as Keycloak, Okta, Auth0, Azure, and other options.

**Steps to Configure External IdP**
1. Go to Core Services → Authentication . 
2. On the landing page, open the External IdP  tab.  
3. In the pop -up page, choose your preferred setup method:  

If you select a provider such as Keycloak, Okta, Auth0, Azure:
- Enter the JSON Web Key Set (JWKS) URL.
- Enter the Issuer or audience if needed.
- Click Save to complete the configuration. 

If you select Others:
- You can select Public URL and enter URL and password.
Or, you can select Upload File and upload certificate (format: .crt, .pfx, .der and file size max 2 MB).
- Enter the Issuer or audience if needed in both cases.
- Click Save to complete the configuration.
