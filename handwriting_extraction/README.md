# Handwriting redaction trained by synthetic data from _Hong et al._

## Installation

To install all necesssary dependencies, install a virtual environment in Conda by typing

    conda create -n handwriting_unet python=3.7.6

then type

    pip install -r requirements.txt

Depending on your conda version, Python=3.7.6 may not be available.
## Create synthetic data

First, all of the necessary training data must be created. For handwriting sentences and words, please go to https://fki.tic.heia-fr.ch/databases/iam-handwriting-database and download sentences and words. These are placed as individual png files in two folders, one for words and one for sentences. For lines and circles, go to https://github.com/googlecreativelab/quickdraw-dataset and download the .npy files for circles and lines. For arrows, go to https://zenodo.org/records/259444 and download and find the mathematical symbols `\rightarrow`, `\uparrow`, `\downarrow`, `\leftarrow`, `\longrightarrow` and `\longleftarrow`. You also may need to resize these images if needed. For digits, download from https://archive.ics.uci.edu/dataset/178/semeion+handwritten+digit.

Second, find and download good background images to overlay the foreground handwritten images on. This will depend on th domain of your documents, but it may include handwriting-free document images from the Industrial Documents Library from UCSF, selected documents from your own archive, or examples from the web.

Third, use example notebooks `create_synthetic_examples.ipynb`, and `create_form_examples.ipynb` to create synthetic training (and evaluation) data. `create_form_examples.ipynb` uses predetermined locations to fill with handwritten text (e.g. forms from https://openaccess.thecvf.com/content_WACV_2020/html/Aggarwal_Multi-Modal_Association_based_Grouping_for_Form_Structure_Extraction_WACV_2020_paper.html).

You'll see that there will be three types of training data:

- `_gt` refers to the ground truth (just handwriting)
- `_tr` refers to the background image with the foreground image
- `_orig` refers to the original background image

## Train

After all of the synthetic data has been created, type

    CUDA_VISIBLE_DEVICES=0  python train.py --model [name to save model] --train-folder [training example folder] --validation-folder [validation example folder] --gpu 1 --bs 32 --train-steps 5 --valid-steps 1 --train-samples 8000 --valid-samples 700 --lr 0.0001

Make sure to change the image width/height inside the `train.py`.

No multi-gpu training is allowed in this setup. Depending on how many CUDA-enabled devices there are, you may need to modify CUDA_VISIBLE_DEVICES.

The model output hdf5 can be converted to pb form using `gerador_hdf5_pb_pbtxt.py`.

# Evaluation

Evaluation metrics can be determined using `segmentation_metrics.ipynb` and you can run inference (handwriting removal) using `remove_handwriting.ipynb`.
