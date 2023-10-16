#!/usr/bin/env cwl-runner

cwlVersion: v1.0
class: Workflow

inputs:
  workspace: Directory
  mets: File
  img_dir: string
  bin_dir: string
  crop_dir: string

steps:
  binarize:
    run: ocrd-cis-ocropy-binarize.cwl
    in:
      workspace: workspace
      mets: mets
      indir: img_dir
      outdir: bin_dir
    out: [bin_outdir]
  crop:
    run: ocrd-anybaseocr-crop.cwl
    in:
      workspace: workspace
      mets: mets
      indir: binarize/bin_outdir
      outdir: crop_dir
    out: [crop_outdir]
    
outputs: []
