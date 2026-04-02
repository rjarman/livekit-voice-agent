---
sidebar_position: 3
---
import CopyPageButton from '@site/src/components/Copy';

# MFA 

<CopyPageButton inidividual= {true}/>

## Overview

Multi-Factor Authentication in Blocks Cloud is a key security capability designed to add an extra layer of protection to user accounts and Construct projects. By requiring users to verify their identity through multiple factors—such as email verification codes or authenticator apps—MFA significantly reduces the risk of unauthorized access, even if primary credentials are compromised.

The MFA service allows administrators to easily enable, disable, and manage various authentication factors directly from the IAM settings. Once enabled, users can configure their preferred MFA method from their individual profiles. Administrators also have full control over email templates used for MFA verification, ensuring a consistent and branded user experience.

:::note
MFA is disabled by default 
:::
 
## Enable or Disable MFA by Email  
1. Go to Core Services → MFA  under IAM section . 
2. Click the three -dot menu  beside Email . 
3. Select Enable  to activate MFA via email.  
 → Once enabled, users can configure MFA from  their profile . 
4. To disable , click the three -dot menu  again and select Disable . 
 
![MFA](/img/MFA1.png "MFA")

**Edit Email Template**
- Click the three -dot menu  beside Email , then select Edit Template . 
- Use the built -in rich text editor  to modify and preview the email sent for MFA 
verification.  
- Click Save  to apply changes.  
 
![MFA](/img/MFA2.png "MFA via Email")  

To learn more about email templates visit [Email](https://docs.seliseblocks.com/cloud/utilities/email)

## Enable or Disable MFA by Authenticator App  
- Go to Core Services → MFA  under IAM section .
- Click the three -dot menu  beside the Authenticator  App
- Select Enable  to activate MFA using an authenticator app (e.g., Microsoft 
Authenticator  app ). After enabling, users can configure  a one -time password (OTP) from their profile.
- To disable , click the three -dot menu  again and select Disable . 
View Swagger link  by clicking API Docs.  
