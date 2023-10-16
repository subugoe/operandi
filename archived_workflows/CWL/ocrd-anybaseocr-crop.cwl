#!/usr/bin/env cwl-runner
cwlVersion: v1.0
class: CommandLineTool
baseCommand: ocrd-anybaseocr-crop
arguments: ["--overwrite"]

inputs:
  workspace:
    type: Directory
    inputBinding:
      prefix: -w
  mets:
    type: File
    inputBinding:
      prefix: -m
  indir:
    type: string
    inputBinding:
      prefix: -I
  outdir:
    type: string
    inputBinding:
      prefix: -O

outputs:
  crop_outdir: 
    type: string
    outputBinding: 
      outputEval: $(inputs.outdir)
