# User Documentation
This document aims to guide users who want to use the Operandi service deployed as a service by an institution.

## 1. Prerequisites

### 1.1 Operandi Account
Before being able to do anything with Operandi, a user must register using the registration endpoint and contact the 
Operandi team to get their account verified and approved. Once the account is approved, the user can access and use all 
other Operandi endpoints.

## 2. Operandi Server endpoints
The Operandi Server is responsible for accepting requests related to `users`, `workspaces`, `workflows`, and 
`workflow job` resources.

A user (i.e., client) would usually send requests in the following order:
1. The user uploads a workspace of images in the [OCRD-ZIP](https://ocr-d.de/en/spec/ocrd_zip) and receives a 
unique `workspace_id` as a response.
2. The user uploads a Nextflow script and receives a unique `workflow_id` as a response.
3. The user starts a workflow job by specifying which workflow (i.e., `workflow_id`) should be executed on which 
workspace (i.e., `workspace_id`). The user should also mention which file group of images should be used as an entry 
point to the workflow. The default file group is `DEFAULT`. The response is a unique `workflow_job_id`.
4. The user polls the workflow job status using the `workflow_job_id` (till it fails or succeeds).
5. The user downloads the workspace results as an [OCRD-ZIP](https://ocr-d.de/en/spec/ocrd_zip) using the 
`workspace_id`.
6. The user downloads the workflow job execution metadata as a zip using the `workflow_job_id`.

## 3. Operandi Client (Python)
The Operandi Python client is useful for users who want to programmatically send requests to the Operandi Server.
That client is also utilized by the Harvesting module.

## 4. Operandi Integration Script (Bash)
The Operandi Integration Script (written in bash) is made to integrate Operandi with other services such as Goobi and 
Kitodo. It can also be used as a client to Operandi. Check the official repo 
[here](https://github.com/subugoe/Operandi-Integration-Script).

## 5. Ola-HD service as a front-end to Operandi Server

The [Ola-HD](https://ola-hd.ocr-d.de/) service also provides a front-end to the Operandi Server. 
The steps are:
1. Login to the Ola-HD service
2. Import a workspace
3. Find the imported workspace
4. Click the `Run Operandi` button
5. Confirm the execution of the job

Note: Keep in mind that the front-end by Ola-HD is convenient for the general non-tech user but may be much less 
flexible when it comes to deciding about the parameters of a job, such as: CPUs, RAM, partition, and the workflow to be 
used.

## 6. Frequently Asked Questions

TODO: Add more information here

This section is separated into further subsections to ease the navigation

### 6.1 Operandi Server endpoints related

### 6.2 Workspaces

### 6.3 Workflows

### 6.4 OTON Converter

### 6.5 Workflow jobs

### 6.6 Other
