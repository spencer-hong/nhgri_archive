# Entity recognition & disambiguation

### Installation

The requirements are listed in [`requirements.txt`](requirements.txt). Furthermore,

    pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2

is required.

This assumes Linux installation and a NVIDIA CUDA driver of 11.7. Modify at your own will based on your system.

### Labeling

This training script requires that you label at least 500 samples with the following categories: PERSON (names of people), ORG (names of organizations), IDNUM (numeric identifiers such as SSNs, credit card numbers, etc), EMAIL (email addresses), and LOC (physical/mailing addresses).


### Train

This code assumes that you have text extracted as described in [start_here.ipynb](../start_here.ipynb).

[`entity_recognition.cfg`](entity_recognition.cfg) is the custom label configuration file for LabelStudio, which can be served either through Tiramisu or independently (see https://labelstud.io/).

[`create_entity_recognition_datasets.ipynb`](create_entity_recognition_datasets.ipynb) steps through creating datasets with holdout evaluation sets upto 500 training examples. This requires that you have annotated at least 500 examples through LabelStudio.

[`train.cfg`](train.cfg) is the custom spaCy training configuration file. Note that total maximum training steps are set at 20,000 steps with early stopping.

[`train.sh`](train.sh) is the bash script to train all of the models necessary to recreate the performance curve, like one below.

### Evaluate

Follow [`evaluate_models.ipynb`](evaluate_models.ipynb) to run evaluations on holdout sets after training.

### Multimodal labeling interface

If you wish to label with both image and text modalities present, you can use the [`image_and_text_entity_recognition.cfg`](image_and_text_entity_recognition.cfg) as the configuration file for LabelStudio. Note that you will need to provide both data points (text and image). To ensure low latency and storage efficiency, you can serve the image by a local file server. A task json for LabelStudio will look like the following:

    {
    "id": 1,
    "data": {
      "ocr": "http://localhost:8081/f/b/b/ffbb0000/ffbb0000_page_0.png" # an example URL from the static file server served on port 8081,
      "text": # OCR text that accompanies the specific image
    }
