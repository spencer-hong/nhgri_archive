# A digital archive reveals how a funding agency cooperated with academics to support a nascent field of science

### Get started

This repository foremost is a preservation effort of the work done associated with this manuscript. We also made an effort to make the analyses done here as reproducible as possible and the code used here is mainly tailored for the Core Collection of the NHGRI archive. During the preparation of this manuscript, we have obtained NSF funding to create a consortium that will support archives across many scholarly discplines. Upon anticipation, we have already started the next development of the technical platform that contains a production-level DAG system with pipeline scheduler and fully Pythonic objects that represent archival artifacts. For more information and ability to test this platform, please visit www.studieddigitally.org. In the meanwhile, we have provided tutorials and an example dataset below. 

### Data
Due to legal constraints enforced by the data transfer agreement with NHGRI, we cannot make certain intermediate data cached files and annotations available freely. However, along with the Core Collection, some annotations are available by request. In the code, we explicitly state sections that require these annotations and how one could arrive at those annotations for themselves or for another archive. Any request for access to the Core Collection or the annotations used here can follow the steps listed in the data availability section of our manuscript:

> Access to the Core Collection and secondary data can be requested from NIH-NHGRI, and its History of Genomics Program by emailing nhgrihistory@mail.nih.gov or Christopher R. Donohue (corresponding author) directly to begin the access request process and to view, without obligation, any data access form. Ownership of the data resides with NIH, and our complementary research into ethics31 identified the need to protect the privacy of individuals contained in the archive. The present MTA further serves to elevate data security and ensure legal liability. Access has hitherto been granted to around two dozen academic institutions in response to approved research requests over the last eight (8) years.  The History of Genomics Program, Office of Communications and the Technology Transfer Office (TTO) of the NHGRI can elect, based on the strength of the proposed research questions, as well as other considerations such as project sustainability, publication record of investigators, and anticipated uses of the data, to enter into a research collaboration agreement with the researcher and their institution. After such an agreement is ratified by both the NHGRI and the relevant researcher institution, the requesting investigator has access to both the “Core Collection” data and the associated metadata for a period of up to three (3) years.  Interested researchers may also apply to the NIH’s Special Volunteer program, as another way of accessing this data.

### Tutorials
**Start at [start_here.ipynb](start_here.ipynb)** to understand and start the pipeline. 

This repository is roughly divided into three sections: Docker-based system to keep track of archival files ([`tiramisu`](tiramisu/README.md)), training and inference scripts for handwriting extraction & entity recognition ([`handwriting_extraction`](handwriting_extraction/README.md) and [`entity_recognition`](entity_recognition/README.md)), and figure-specific code. Code regarding specific figures are in `figure_{}` folders. 

Because the NHGRI archive is by request, for this tutorial, example data is sourced from the [Industry Documents Library](https://www.industrydocuments.ucsf.edu/) under Fair Use. This is located in [`example_data`](example_data/). 

Some figures in the manuscript can be regenerated without access to the Core Collection. For example, the decision model from Figure 4 can be created without any intermediary or archival files from NHGRI. We provide the decision dataset as supplementary data.

### Contact & Main author/developer

Spencer Hong (spencerhong [at] u.northwestern.edu)   

### Corresponding Authors
Thomas Stoeger (stoeger [at] northwestern.edu)  
Luis Amaral (amaral [at] northwestern.edu)   
Christopher Dononhue (christopher.donohue@n [at] nih.gov)

