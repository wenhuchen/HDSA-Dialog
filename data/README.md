# Data File Description


## Meta File
- belief_state.json: Listing all the possibel belief state, used as constraints to do DB search.
- vocab.json: The shared vocabulary of both the predictor and the generator.
- test_reference.json: The delexicalized reference file for test set, used to calculate BLEU score.
- test_reference_nondelex.json: The non-delexicalized reference file for test set, used to calculate the raw BLEU score.
- act_ontology.json: Listing the 600+ possible dialog acts, all in a triple format, consiting of domain, function and arguments.

## Training Predictor
- train, dev, tet.tsv: The files are for training the predictor, the first field is the dialog id, second field is the turn id, the third field is the naturalized DB query result, the fourth field is the last round system response, the fifth field is the current round user query. The last field is the graph representation of the ground truth dialog acts.

## Training Generator
- train, val, test.json: The files are for training the generator, is is a list of dialogs, every dialog is represented with a dictionary, with file field containing the dialog id, info field containing the multiple rounds. Each round is further represented with a dictionary, containing current round "delexicalized user query", "raw user query", "dialog acts", "belief state", "KB (the number of entries in the KB which meet the requirement of current BS constraint)" and the "source (the selected row among the queries results, recovered from the system response.)".
```
[
  {
    file: XXX,
    info: {
      [ # Round 1
        sys:
        user:
        BS:
        ACT:
        KB:
      ],
      [ # Round 2
        sys:
        user:
        BS:
        ACT:
        KB:
      ]
      ....
    }
  }
  ...
]

```
