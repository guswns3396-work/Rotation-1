"""ihs_causal: fast, modular causal excursion-effect analysis for the IHS micro-randomized trials.

Layers (each is a small subpackage with a registry, so new pieces plug in without touching the others):
  data        decision tables, hourly streams and outcome windows, cached as Parquet
  design      contrasts: which rows, which arms, which randomization probabilities
  estimators  weighted least squares core, WCLS, DR-WCLS, nuisance learners, inference
  runner      expands a YAML configuration into runs and stores every estimate with provenance
  viewer      turns the results store into one self-contained HTML file
"""
__version__ = "0.2.1"
