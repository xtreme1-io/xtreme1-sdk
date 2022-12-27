# xtreme1 export to coco
This is script to convert Xtreme1 standard format to coco format

## How to use

### 1.Export
Export the annotation results of xtreme1(xxx.zip)

    D:\
    ├── xtreme1-20221223064438.zip 
    └── save_folder
### 2.Setup
    pip install numpy opencv-python tqdm
### 3.Usage
    python Xtreme1_V0.5.5_export_coco.py <zipfile> <save_folder>
    // zipfile : The zip file exported by xtreme1
    // save folder : The path where the conversion results are saved
    // Note that the resulting save directory needs to be an empty folder
### 4.Example of usage
    python Xtreme1_V0.5.5_export_coco.py D:\xtreme1-20221223064438.zip  D:\save_folder
Final directory structure
    
    D:\
    ├── xtreme1-20221223064438.zip 
    └── save_folder
            └── x1 dataset xtreme1 annotations
                    └── coco_results.json  // coco format json






