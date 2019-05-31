# HDSA-Dialog
This is the code and data for ACL 2019 long paper "Semantically Conditioned Dialog Response Generation via Hierarchical Disentangled Self-Attention". The up-to-date version is in [http://arxiv.org/abs/1905.12866](http://arxiv.org/abs/1905.12866).

The full architecture is displayed as below:
<p>
<img src="resource/full_architecture.png" width="800">
</p>

The architecture consists of two components:
- Dialog act predictor (Fine-tuned BERT model)
- Response generator (Hierarchical Disentangled Self-Attention Network)

The basic idea of the paper is to do enable controlled reponse generation under the Transformer framework, where we construct a dialog act graph to represent the semantic space in MultiWOZ tasks. Then we particularly specify different heads in different levels to a specific node in the dialog act graph. For example, the picture above demonstrates the merge of two dialog acts "hotel->inform->location" and "hotel->inform->name". The generated sentence is controlled to deliever message about the name and location of a recommended hotel. 

## Requirements
- Python 3.5
- [Pytorch 1.0](https://pytorch.org/)
- [Pytorch-pretrained-BERT](https://github.com/huggingface/pytorch-pretrained-BERT)


## Dialog Act Predictor
This module is used to predict the next-step dialog acts based on the conversation history. Here we adopt the state-of-the-art NLU module [BERT](https://arxiv.org/abs/1810.04805) to get the best prediction accuracy.



## Reproducibility
- We release the pre-trained predictor model in [google drive](https://drive.google.com/open?id=1x2K07nMEFrmbzPZNNbJ6M93dE3EYcS-0), you can put the zip file into checkpoints/predictor and unzip it to get the save_step_15120 folder.
- We already put the pre-trained generator model under checkpoints/generator, you can use this model to obtain 23.6 BLEU on the delexicalized test set.

