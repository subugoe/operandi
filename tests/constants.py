BATCH_SCRIPT_EMPTY = "test_empty.sh"
WORKFLOWS_ROUTER_DIR = "workflows"
WORKSPACES_ROUTER_DIR = "workspaces"
WORKFLOW_DUMMY_TEXT = """ocrd process \n
     "cis-ocropy-binarize -I OCR-D-IMG -O OCR-D-BIN" \n
     "anybaseocr-crop -I OCR-D-BIN -O OCR-D-CROP" \n
     "skimage-binarize -I OCR-D-CROP -O OCR-D-BIN2 -P method li" \n
     "skimage-denoise -I OCR-D-BIN2 -O OCR-D-BIN-DENOISE -P level-of-operation page" \n
     "tesserocr-deskew -I OCR-D-BIN-DENOISE -O OCR-D-BIN-DENOISE-DESKEW -P operation_level page" \n
     "cis-ocropy-segment -I OCR-D-BIN-DENOISE-DESKEW -O OCR-D-SEG -P level-of-operation page" \n
     "cis-ocropy-dewarp -I OCR-D-SEG -O OCR-D-SEG-LINE-RESEG-DEWARP" \n
     "calamari-recognize -I OCR-D-SEG-LINE-RESEG-DEWARP -O OCR-D-OCR -P checkpoint_dir qurator-gt4histocr-1.0\""""
