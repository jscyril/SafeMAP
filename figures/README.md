# SafeMAP paper figures

## Conversion pipeline

`safemap_conversion_pipeline.svg` is the editable source for the paper's
conversion-pipeline figure. It is designed as a full-width, two-column IEEE
figure and remains legible in grayscale.

Generate the paper-ready derivatives with:

```bash
make figures
```

Suggested LaTeX:

```tex
\usepackage{graphicx}

\begin{figure*}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/safemap_conversion_pipeline.pdf}
  \caption{SafeMAP's safe-first conversion and acceptance pipeline. Static
  analysis first separates analyzer eligibility from implemented synthesis
  support. The main lane generates Rust directly from an auditable migration
  plan, while C2Rust runs separately as a baseline/reference lane. Both outputs
  face the same strict policy gate; unsupported, synthesis-missing, and
  validation-failed outcomes are retained rather than counted as successful
  migration.}
  \label{fig:safemap-pipeline}
\end{figure*}
```
