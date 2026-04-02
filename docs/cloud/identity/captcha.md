---
sidebar_position: 4
---
import CopyPageButton from '@site/src/components/Copy';

# CAPTCHA

<CopyPageButton inidividual= {true}/>

## Overview

The CAPTCHA service adds an essential security layer to your Construct applications by distinguishing real users from automated bots. By integrating CAPTCHA validation into your authentication flow, you protect your system from spam, credential-stuffing attempts, and other automated attacks. The platform supports industry-standard providers such as Google reCAPTCHA and hCaptcha, allowing you to choose the solution that best fits your security needs.

:::note
By default, no CAPTCHA configuration is set. It can be enabled in two ways.  
:::

## Add CAPTCHA  

### For Google reCAPTCHA  
1. Go to the Google reCAPTCHA  website.  
2. Enter your domain  in the corresponding field.  
3. Click the Submit/Send  button.  
4. Once registered, you will receive a Site Key  and a Secret Key. 
5. Go to Core Services → CAPTCHA  in Blocks Cloud  under IAM section. 
6. Click Add Configuration. 
7. Select reCAPTCHA  from the dropdown menu.  
8. Enter the Site Key  and Secret Key  collected from Google.  
9. Click Save  to complete the setup.  
 
![Captcha](/img/Captcha1.png "Google reCAPTCHA ")

### For hCaptcha  
1. Go to Core Services → CAPTCHA . 
2. Click Add Configuration . 
3. Select hCaptcha  from the dropdown menu.  
4. Enter the required Site Key  and Secret Key . 
5. Click Save  to apply the configuration.  
 
![Captcha](/img/Captcha2.png "hCaptcha") 

## Important: Update the .env File

Please make sure to add the Captcha Site Key and Captcha Type in your .env file of Construct. This ensures the application can access your configuration properly.

![Captcha](/img/Captcha3.png ".env file")

:::note
A single provider (e.g., reCAPTCHA or hCaptcha) can only be configured once.  
:::

:::note
Only one CAPTCHA can be enabled at a time.   
:::

