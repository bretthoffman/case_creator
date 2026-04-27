# Case Creator Rules Editing Guide

This folder contains the main business rules file for Case Creator.

## The file you edit

Edit this file:

`business_rules/v1/case_creator_rules.yaml`

Do **not** edit the packaged seed file by hand.

---

## How to make changes with ChatGPT

### Step 1 — Open the prompt file

Open:

`business_rules/v1/CASE_CREATOR_RULES_EDIT_PROMPT.md`

Copy the **entire contents** of that file.

---

### Step 2 — Add your requested change

At the very bottom of the prompt file, there is a line that says:

`NEW CHANGES I WANT TO MAKE:`

Describe what your requested change is after that line.

Examples:
- Turn contact model mode on
- Add A3.5 to the non-Argen shade markers
- Add a doctor rule so Dr Jane Doe always goes to ai_envision
- Route the AI family to argen

---

### Step 3 — Paste the full YAML file after the prompt

Open:

`business_rules/v1/case_creator_rules.yaml`

Copy the **entire contents** of that YAML file.

Then paste that full YAML file **underneath** the prompt in the ChatGPT message.

So the message you send should contain:

1. the full prompt file  
2. your requested change added after `NEW CHANGES I WANT TO MAKE:`  
3. the full current YAML file pasted below it  

---

### Step 4 — Let ChatGPT respond

If your request is clear, ChatGPT should return:

- the **full updated YAML file**
- in **one code block**
- with **no extra explanation**

If your request is not clear enough, it should ask you a short follow-up question first.

Answer the question, then let it generate the full updated YAML.

---

### Step 5 — Replace the YAML file

Copy the **entire YAML code block** from ChatGPT’s response.

Paste it back into:

`business_rules/v1/case_creator_rules.yaml`

Replace the whole file.

Save it.

---

### Step 6 — Restart the app

After saving the file:

**RESTART THE APP**

Changes do not take effect until the app is restarted.

---

## Important rules

- Always paste the **entire** prompt file first
- Always paste the **entire** current YAML file after the prompt
- Always replace the **entire** YAML file with the response
- Do not hand-edit random parts unless you understand the format
- Do not invent new keys or sections yourself
- Do not remove header comments from the YAML file

---

## What kinds of changes can be made

This YAML file supports changes such as:

- doctor override rules
- advanced doctor outcome rules
- non-Argen shade markers
- routing overrides
- Argen contact-model mode on/off

Examples of possible requests:

- “Turn contact model mode on.”
- “Add A3.5 to the non-Argen shade markers.”
- “Route the AI family to argen.”
- “Add a simple doctor rule so Dr Smith always uses ai_envision.”

---

## If something goes wrong

If ChatGPT returns something that:

- looks incomplete
- removes large sections
- changes unrelated rules
- invents new fields
- does not return the full YAML file

do **not** save it yet.

Instead, try again with a clearer request.

---

## Final reminder

The normal workflow is:

1. Copy the prompt file
2. Add your requested change at the end
3. Paste the full current YAML file below it
4. Send to ChatGPT
5. Copy the full YAML response back into `case_creator_rules.yaml`
6. Save
7. Restart the app