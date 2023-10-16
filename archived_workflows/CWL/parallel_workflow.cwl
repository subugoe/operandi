#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow

requirements:
 ScatterFeatureRequirement: {}
 SubworkflowFeatureRequirement: {}

inputs:
  subspaces_array: Directory[]
  mets_array: File[]
  img_dir: string
  bin_dir: string
  crop_dir: string

steps:
  subworkflow:
    run: 
      class: Workflow
      inputs: 
        subspace: Directory
        mets_file: File
        img_dir: string
        bin_dir: string
        crop_dir: string
      outputs: []   
      steps:
        binarize:
          run: ocrd-cis-ocropy-binarize.cwl
          in:
            workspace: subspace
            mets: mets_file
            indir: img_dir
            outdir: bin_dir
          out: [bin_outdir] 
        crop:
          run: ocrd-anybaseocr-crop.cwl
          in:
            workspace: subspace
            mets: mets_file
            indir: binarize/bin_outdir
            outdir: crop_dir
          out: [crop_outdir]         
    scatter: [subspace, mets_file]
    scatterMethod: dotproduct
    in: 
      subspace: subspaces_array
      mets_file: mets_array
      img_dir: img_dir
      bin_dir: bin_dir
      crop_dir: crop_dir
    out: []
    
outputs: []
