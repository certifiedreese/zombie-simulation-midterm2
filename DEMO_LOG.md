# Demo Log

## Demo 1: Ontology validation
- Correct ontology: Ontology OK: 4 classes, 2 relations, 6 constraints.
- Broken ontology ("to": "Humans"):
  ONTOLOGY INVALID: Relation 'bites' has unknown 'to' class 'Humans'
- Result: the pipeline catches a mistake in the rulebook before
  the AI ever sees it.