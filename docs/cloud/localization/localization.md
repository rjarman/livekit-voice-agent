---
sidebar_position: 1
---

import CopyPageButton from '@site/src/components/Copy';

# Localization 

<CopyPageButton inidividual= {true}/>

**Localization** is a core service within the Blocks Cloud 
platform. It allows users to easily configure and manage multilingual interfaces for their projects. With the language section, anyone can quickly add and switch between multiple languages on their websites or applications —without complex coding or manual setup.     
    
## Add a Language

You can easily add and manage the languages you want to use on your website directly 
from our interface.  

### Add a New Language  

1. Click Configure Language  from the Language dashboard.  
2. On the language configuration page, click New Language . 
3. Select your desired language from the dropdown menu.  
4. Click Save . 
The new language will now be added alongside your existing languages.  

### Delete a Language    

1. Find the language you want to remove.  
2. Click the three-dot menu ( ⋮) next to it.  
3. Select Delete  

### Set a Default Language  

1. Find the language you want to set as default.  
2. Click the three-dot menu ( ⋮) next to it.  
3. Select Make Default Language

## Keys and Modules  

Setting a value for a key is an important part of the process. For each key, you assign a specific word or sentence in your UI. Later, when you want to display the same content in another language, you simply provide a translation for that key in the new language. In this service, you can see a section called Module. We can place our keys inside any module we want. The main advantage of this is that it keeps things segmented and organized.  

For example, under the auth  module, we can store all authentication-related keys. Or we can create a common  module to store keys that are used across multiple parts of the website. So, the module names can be created based on the specific needs and structure of each website.  

:::note
There are many keys and modules already built for you. These are all mapped to the texts in the Construct front-end app. You can choose to edit them as you wish.
:::

### Add a New Key  
1. Click the New Key  button.  
2. In the About the Key  section, enter a key name.  
    a. It’s best to name the key based on the word or sentence it represents.  
    b. Example: If your sentence is “Hello World,” the key name can be hello_world. 
3. Select an existing module from the dropdown or create a new module.  
4. Add the default value (English) for that key.  
5. Click Save  or continue to the next section.  
6. In the Translations  section, find the language you want to translate into.  
7. Click the Auto Translate  button next to that language.  
8. Review and click Save.  

### Edit or Delete a Key  

You can easily edit or delete any key from the Language interface.  

**Edit a Key**

1. Go to the Language Landing Page . 
2. In the Translations  section, search for the key you want to edit.  
3. Click on the key — the Edit Key  page will open.  

Under the Details tab:  
- Click Edit  next to English, update the text, and click Save . 
- To edit any other language, click Edit  beside that language, then click Auto 
Translate . Once the translation is complete, click Save . 

From the Edit Key  page, you can also:  
- Click the three-dot menu ( ⋮) and select Auto Translate  to translate the key into all 
available languages at once.  
- To change the translation prompt, include:
  1. What the text represents (UI label, button, tooltip, etc.)
  2. Its purpose or function
  3. Any tone/style preference (formal, casual, friendly, technical, etc.)
  4. Click Save → Now when you auto-translate, GPT will use this context and give a much more accurate, relevant translation than a generic one.
   
**Revert a Key**  
1. Go to the Edit Key  page.  
2. Under the History  tab, click the Revert  button.  
The key’s translation will return to its previous version if there is any.

![Language](/img/uilm1.png "Language")
 
**Delete a Key**  
1. Go to the Language Landing Page . 
2. In the Translations  section, search for the key you want to delete.  
3. Click on the key — the Edit Key  page will open.  
4. From the three-dot menu ( ⋮), select Delete Key  and confirm the action.  

**New Module**
1. On the Landing Page , click the three-dot menu ( ⋮). 
2. Select New Module . 
3. Enter the module name and click Save . 


:::note  
While creating a new key, you can also add a new module directly from the module  dropdown.  
:::
   
**Configure AutoTranslate All**
1. On the Landing Page , click the three-dot menu ( ⋮). 
2. Select Auto Translate All . 
3. A pop-up notification saying “Processing Translation”  will appear.  
4. Once the process is complete, all keys which are not translated yet will be 
translated from the default language to all other available languages.  

## Import Keys  

You can upload multiple keys at once by importing a file. This helps you quickly add or 
update large sets of keys.  
File Requirements  
- Maximum file size:  50 MB  
- Supported formats:  .xlsx , .csv , .json 

![Language](/img/uilm2.png "Language")

**Steps to Import Keys**

1. On the Landing Page , click the three-dot menu ( ⋮). 
2. Click Template  if you want the template to import data in JSON format.  
3. Upload your file or drag and drop it into the upload area.  
4. Click Save  to import all keys.  

### Export Keys  
You can download your keys from the Language section to save a backup or use them for offline editing.    

**File Requirements:**
- Maximum file size:  50 MB  
- Supported formats:  .xlsx , .csv , .json 
 
**Steps to Export Keys**
1. On the Landing Page , click the three-dot menu ( ⋮). 
2. Select Export Keys . 
3. Choose the modules you want to export:  
    a. Click individual checkboxes for specific modules, or  
    b. Click Select All  to export all modules.  
4. Select your preferred file format from the available options ( .xlsx , .csv , .json ). 
5. Click Export . 
A download success notification will appear once the export is complete.  

### Export History  

You can view and download all export history directly from the UI.  

**Steps to View and Download Export History**  
1. On the Landing Page , click the three-dot menu ( ⋮). 
2. Select Export History . You will be redirected to a page listing all past exports.  
3. Use the search or date filter to find specific exports.  
4. Click Download  next to any export to save it again to your device.    

### File Formats

When importing your keys, you might have your keys in .xlf format, especially if you are coming from the older version of Blocks. Here is an example of the format that you would have to have your .xlf file in:

|ItemId	|ModuleId	|Module	|KeyName	|bn-BD	|bn-BD_CharacterLength	|de-DE	|de-DE_CharacterLength	|en-US	|fr-FR	|fr-FR_CharacterLength	|it-IT	|it-IT_CharacterLength|
|---|---|---|---|----|----|----|----|----|----|----|----|----|
|946350c5-18e3-4efb-bcda-5874955be3e4|41c96a75-0e14-4df6-bcf0-baf5bcf88f3f|common|LAST_LOGGED_IN|সর্বশেষ লগইন|9|Zuletzt angemeldet.|19|Last Logged in|Dernière connexion.|19|Ultimo accesso|15|

:::note
the default language does not require the character length in the file. In the case above, it is English.
:::

## View Filter  

You can filter and view translations for specific languages directly in the table.  

**Steps to Use View Filter**
1. On the Landing Page , click the View Filter  in the Translations table.  
2. A dropdown will appear showing all available languages.  
3. Click any language to see its details reflected in the table.  
4. To view translations for all languages in the table, click the Translations  option 
from the filter —it will select all languages.  

## Publish Changes  

Once you publish changes, you will be able to see all the edits you made reflected on your 
frontend.  

**Steps to Publish**  
1. On the Landing Page , click the Publish Change filter.  
2. A pop-up box will appear. Click Publish . 
3. A download success notification will appear once it is complete.

## Migrating from the older version of Blocks

If you are migrating to the newer version of Blocks, follow these steps:

1. Create a new account in Blocks Cloud
2. Export your existing keys from the older version of Blocks
    1. Export in .xlsx format
    2. Convert the exported file to the [new format](#file-formats). 
3. If needed, seek Blocks’ assistance to remove existing boilerplate keys.
4. [Import](#import-keys) the .xlsx file in your new Blocks account
5. Publish your changes
6. To integrate the new Language API into your code, follow these guides:
    - [Get started with the new API](https://docs.seliseblocks.com/reference/)
    - [Get configured languages](https://docs.seliseblocks.com/reference/localization/Get%20Available%20Language)
    - [Get Language file](https://docs.seliseblocks.com/reference/localization/Get%20Language%20File)


:::note
To migrate from one environment to another environment, please follow [Environment Migration](https://docs.seliseblocks.com/cloud/getting-started#environment-selection)
:::
