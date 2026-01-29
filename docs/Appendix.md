# Workflows Execution Time Comparison

<img width="1008" height="609" alt="image" src="https://github.com/user-attachments/assets/e3f185f3-4e13-4ab6-af92-68393abf068c" />


# Workflows Processors Performance Profiling&nbsp;

<img width="1420" height="823" alt="image" src="https://github.com/user-attachments/assets/dd7c4411-d0a0-4a16-91ae-1bf5428429ac" />


<img width="1420" height="823" alt="image" src="https://github.com/user-attachments/assets/1df0f7d9-fa30-4b97-81d2-e4f20e34b78e" />


<img width="1420" height="824" alt="image" src="https://github.com/user-attachments/assets/06f644c7-ae78-4766-a665-2a2e11a06545" />


<img width="1420" height="823" alt="image" src="https://github.com/user-attachments/assets/31aaf7cc-8ccc-438b-a5c4-8ab84f310f73" />


<img width="1421" height="824" alt="image" src="https://github.com/user-attachments/assets/c933a785-1f15-4012-b251-84a0f9df068a" />


<img width="1421" height="824" alt="image" src="https://github.com/user-attachments/assets/a64928e6-a39c-43c4-87a8-4ffa10803827" />




## Correlation Heatmap 
### Step-level is workflow processor level which aggregate together to perform one job, while Job level is the Overall job metrics.

<img width="1212" height="538" alt="image" src="https://github.com/user-attachments/assets/1ce8568b-ba1f-465f-b2fb-6686f0196221" />




# Resource Prediction Results

## Direct vs. Aggregated Job Prediction Approaches

*   **Direct Job-Level Modeling:** building models directly on whole-job data (treating each job as  
    one data point) and trying to predict the final outcome.
    
*   **Aggregated Step-to-Job Modeling:** Models are built to predict the outcome metrics of each  
    step within the workflow. Then those small steps are aggregated (as shown in the following figure)  
    predictions into an entire Job-Level prediction following certain rules:
    
    *   **For duration**, we summed the predicted durations of steps along each fork and took the  
        maximum over forks.
        
    *   **For peak memory**, we took the maximum predicted peak across all steps of the job.
        
    *   **For I/O**, we summed the predicted bytes across steps.
        
        
        <img width="2804" height="1598" alt="image" src="https://github.com/user-attachments/assets/41610207-0671-481a-8360-22d15a5d1eb7" />

          

## Duration

<img width="2050" height="512" alt="image" src="https://github.com/user-attachments/assets/ca63b721-182e-4129-bf6e-810702c72171" />
<img width="948" height="512" alt="image" src="https://github.com/user-attachments/assets/7c90e967-9a0b-4641-a456-7d737caa1619" />
<img width="739" height="565" alt="image" src="https://github.com/user-attachments/assets/91f8e191-da3e-42b0-b541-2ad46be06a66" />


## Peak RSS

<img width="1652" height="384" alt="image" src="https://github.com/user-attachments/assets/36f886f2-43c9-40f0-95f7-a0a2ae50b467" />
<img width="1016" height="512" alt="image" src="https://github.com/user-attachments/assets/947de0f6-7d94-4cf7-8bba-62464247bf98" />
<img width="722" height="564" alt="image" src="https://github.com/user-attachments/assets/0195b284-0f40-4622-80b5-2f4e47a43fc6" />


## Read Bytes

<img width="1656" height="386" alt="image" src="https://github.com/user-attachments/assets/2a6dfee7-ac7f-4c9a-896d-3eff5dd2dda9" />
<img width="1026" height="372" alt="image" src="https://github.com/user-attachments/assets/cc8e039f-489d-453c-9885-c7a5358c0663" />
<img width="709" height="564" alt="image" src="https://github.com/user-attachments/assets/9f0d3d17-3643-434d-a45a-3c7dc4a9b852" />



## Write Bytes

<img width="1652" height="392" alt="image" src="https://github.com/user-attachments/assets/c827913e-9e7f-4ca9-b17f-6db1e6852164" />
<img width="952" height="512" alt="image" src="https://github.com/user-attachments/assets/5971bcf3-95cc-4368-bcdc-f593624ddf68" />
<img width="709" height="564" alt="image" src="https://github.com/user-attachments/assets/da83b40f-4079-4e81-9a67-82e4846c605f" />

