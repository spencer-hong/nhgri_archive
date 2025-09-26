
import numpy as np



abstract = np.load("../../manuscript/cache/abstract_matched_nhgri_organisms.npy")
title = np.load("../../manuscript/cache/title_matched_nhgri_organisms.npy")
together = np.bitwise_or(abstract.astype(bool), title.astype(bool))

print('abstract and title done')

del abstract, title

keywords = np.load("../../manuscript/cache/keywords_matched_by_nhgri_organisms.npy")

together = np.bitwise_or(together.astype(bool), keywords.astype(bool))

print('keywords done')
del keywords

mesh = np.load("../../manuscript/cache/mesh_matched_by_nhgri_organisms.npy")

together = np.bitwise_or(together.astype(bool), mesh.astype(bool))

print('mesh done')

del mesh

np.save('../../manuscript/cache/all_combined_nhgri_organisms.npy', together)


