<br>

# Workflows Execution Time Comparison

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595928/workflow_runtime_distribution.png"></div></figure>

# Workflows Processors Performance Profiling&nbsp;

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595929/steps_duration_contribution_percentage.png"></div></figure>

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595933/steps_peak_rss_contribution_percentage.png"></div></figure>

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595930/steps_read_bytes_contribution_percentage.png"></div></figure>

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595931/steps_write_bytes_contribution_percentage.png"></div></figure>

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595932/steps_vol_ctxt_contribution_percentage.png"></div></figure>

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/attachments/595934/steps_invol_ctxt_contribution_percentage.png"></div></figure>

#####   

#####   

##### Step-level is workflow processor level which aggregate together to perform one job, while Job level is the Overall job metrics.

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595935/content">

<br>

<br>

<br>

<br>

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
        
        <br>
        
        <br>
        
        <img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595936/content">
        

##   

## Duration

## <img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595937/content">

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595942/content">

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595949/content">

<br>

## Peak RSS

## <img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595938/content">

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595941/content">

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595948/content">

<br>

##   

## Read Bytes

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595939/content">

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595944/content">

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595946/content">

<br>

## Write Bytes

<figure class="image op-uc-figure"><div class="op-uc-figure--content"><img class="op-uc-image" src="/api/v3/attachments/595940/content"></div></figure>

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595943/content">

<br>

<img class="op-uc-image op-uc-image_inline" src="/api/v3/attachments/595945/content">

<br>

<br>

##