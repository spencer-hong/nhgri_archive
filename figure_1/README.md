# Figure 1

### Installation

Due to Doc2Vec and TSNE projections, code in this section requires additional dependencies on top of those in [`entity_recognition`](../entity_recognition/README.md). The additional dependencies are listed in [`requirements.txt`](requirements.txt) and can be installed by

    pip install -r requirements.txt

Make sure that the requirements.txt is the one in this folder.

We also added relationships in Neo4J (Tiramisu) that connect individual PDF pages to documents to represent logical documents in collated PDF files. We represent these as "Document" inside the graph database. The process to arrive at these "Document" objects is described at [`start_here`](../start_here.ipynb).

For stopwords filtering, we follow the instructions in (_Gerlach et al._)[https://github.com/amarallab/stopwords/tree/master]. We use the `code/src` in that repo and place it [here](gerlach_et_al_src).

### Usage

`circle_of_stats.ipynb` creates Figure 1b, the aggregate stats of the corpus.

`date_extraction.ipynb` extracts dates from the text using regex patterns and then creates Figure 1c. This also creates the SI figures including the boxenplot of the projects and the temporal controls.

`doc2vec_training.ipynb` removes stopwords (see _Gerlach et al_) at different thresholds and then trains Doc2Vec models on the corpus text.

`doc2vec_tsne_projection.ipynb` creates TSNE projections (under the parameters optimized for large documents corpus, see **\_**) which creates Figure 1d.