
## Philosophy

The CSF Declarative Annotation system provides a middle path between zero-configuration magic and explicit metadata specification. It allows authors to declare computational artifacts in a simple, readable way that:

1. **Renders invisibly** in plain LaTeX (via comments)
2. **Activates rich linking** when compiled with CSTeX
3. **Maintains readability** in the source document
4. **Supports complex scenarios** that auto-detection cannot handle

## Design Goals

- ✅ **Plain LaTeX Compatibility**: Standard LaTeX compilers ignore CSF annotations completely
- ✅ **CSTeX Enhancement**: CSTeX compiler activates rich hyperlinking and metadata
- ✅ **Readable Syntax**: Annotations are clear and maintainable in source
- ✅ **Gradual Adoption**: Zero-config for figures, opt-in declarations for complex cases

## Annotation Syntax

All CSF annotations use LaTeX comment syntax (`%`) to ensure plain LaTeX compatibility.

### Basic Artifact Declaration

```latex
% CSF-ARTIFACT: type=figure, path=figures/plot.png, step=analysis, script=scripts/analyze.py, line=42
\includegraphics{figures/plot.png}
\caption{Analysis results}
```

### Statistical Output Declaration with Value Inclusion

```latex
# In composable.toml:
# [[pipeline.outputs.values]]
# name = "r1_correlation"
# type = "correlation"
# ...
The correlation coefficient is r = \csfvaluelink{r1_correlation}{float,round2}.
```

### Table Declaration

```latex
# In composable.toml:
# [[pipeline.outputs.artifacts]]
# path = "data/results.csv"
# ...
\begin{table}
\input{data/results.csv}
\csflink{data/results.csv}
\caption{Processed experimental results}
\end{table}
```

### Inline Computation Declaration

```latex
# In composable.toml:
# [[pipeline.outputs.values]]
# name = "mean_temp"
# expression = "mean(data.temperature)"
# ...
The mean temperature was \csfvaluelink{mean_temp}{float,round1}°C.
```

## Plain LaTeX Compatibility Solution

To maintain compatibility with regular LaTeX compilers, CSTeX uses a two-phase approach:

1. **CSF Annotations**: Always in comments (invisible to plain LaTeX)
2. **Fallback Commands**: CSTeX defines no-op versions for plain LaTeX

### Fallback Command Definitions

```latex
% In composable.sty - these commands provide graceful fallbacks
\providecommand{\csfvaluelink}[2]{#2} % Shows format specifier in plain LaTeX
\providecommand{\csflink}[1]{}        % Invisible in plain LaTeX
```

### Enhanced CSTeX Behavior

When CSTeX processes the document, it:
1. **Replaces fallback commands** with rich linking versions
2. **Injects computed values** from pipeline execution  
3. **Generates hyperlinks** to computational context
4. **Validates against pipeline** to ensure accuracy

## Value Inclusion Syntax

For statistical outputs that should include computed values:

```latex
# In composable.toml, you define the value 'r1_correlation'
The correlation is r = \csfvaluelink{r1_correlation}{float,round2}.
```

**Format specifiers:**
- `float,round2` - Show as floating point with 2 decimal places
- `percent,round1` - Show as percentage with 1 decimal place  
- `scientific,round3` - Show in scientific notation
- `int` - Show as integer
- `string` - Show as raw string

### How It Works

**In Plain LaTeX:**
```latex
% Shows placeholder or static value
The correlation is r = \csfvaluelink{r1_correlation}{float,round2}.
```

**In CSTeX:**
```latex  
% Shows computed value with hyperlink
The correlation is r = 0.85[🔗 STAT].
```

## Annotation Types

### 1. Figure Artifacts (`CSF-ARTIFACT`)
```latex
% CSF-ARTIFACT: type=figure, path=figures/histogram.png, step=visualization, script=scripts/plot.py, line=34
\includegraphics{figures/histogram.png}
```

### 2. Statistical Outputs (`CSF-STAT`) 
```latex
% CSF-STAT: name=pvalue1, type=p_value, step=testing, script=scripts/ttest.py, line=67
% CSF-STAT: name=corr1, type=correlation, step=analysis, script=scripts/corr.py, line=23
% CSF-STAT: name=mean1, type=mean_std, step=summary, script=scripts/describe.py, line=15
```

### 3. Table Data (`CSF-TABLE`)
```latex
% CSF-TABLE: path=outputs/summary.csv, step=aggregation, script=scripts/summarize.py, line=89
\input{outputs/summary.csv}
\csftablelink{outputs/summary.csv}{aggregation}
```

### 4. Inline Computations (`CSF-COMPUTE`)
```latex
% CSF-COMPUTE: name=accuracy, expr="model.score(X_test, y_test)", step=evaluation, script=scripts/eval.py, line=12
Model accuracy: \csfstatlink{accuracy}{percent,round1}
```

## Enhanced LaTeX Commands

### Statistical Enhancement with Value Inclusion
```latex
% Original LaTeX:
% CSF-STAT: name=r1_correlation, type=correlation, step=analysis, script=scripts/analyze.py, line=45
The correlation is r = \csfvaluelink{r1_correlation}{float,round2}.

% Plain LaTeX Output:
The correlation is r = float,round2.

% CSTeX Enhanced Output:
The correlation is r = 0.85[🔗 STAT].
```

### Table Enhancement with Compatibility
```latex
% Original:
% CSF-TABLE: path=data/results.csv, step=processing
\input{data/results.csv}
\csflink{data/results.csv}

% In plain LaTeX: \csftablelink does nothing (invisible)
% In CSTeX: \csftablelink generates rich provenance link
```

## Example Document

```latex
\documentclass{article}
\usepackage{graphicx}
\usepackage{amsmath}
% composable package auto-injected by CSTeX

\title{Computational Results with CSF Declarations}
\author{Research Team}

\begin{document}

\section{Analysis}

% CSF-ARTIFACT: type=figure, path=figures/correlation.png, step=analysis, script=scripts/analyze.py, line=67
\begin{figure}
\includegraphics[width=0.8\textwidth]{figures/correlation.png}
\caption{Temperature vs Pressure correlation analysis}
\end{figure}

% CSF-STAT: name=main_correlation, type=correlation, step=analysis, script=scripts/analyze.py, line=45
Our analysis revealed a strong correlation (r = \csfvaluelink{main_correlation}{float,round2}) between temperature and pressure.

This correlation is statistically significant (p < \csfvaluelink{significance_test}{scientific,round3}).

\begin{table}
\input{outputs/summary_stats.csv}
\csflink{outputs/summary_stats.csv}
\caption{Summary statistics for experimental conditions}
\end{table}

The final model achieved an accuracy of \csfvaluelink{final_accuracy}{percent,round1} on the test set.

\end{document}
```

## Compatibility Results

**Plain LaTeX Compilation:**
- Document compiles normally
- CSF comments are ignored
- `\csfstatlink{name}{format}` shows the format string as placeholder
- `\csftablelink` is invisible

**CSTeX Compilation:**
- All CSF annotations are processed
- Values are computed from pipeline execution
- Rich hyperlinks are generated
- Dashboard integration is enabled

This approach provides the best of both worlds: **explicit declarative control** with **complete plain LaTeX compatibility**.

## 5. Pre-flight Checklist

To enhance the robustness of the CSF, we will introduce a "pre-flight checklist" that distinguishes between "compiling" and "analyzing." This will be an extension of our CLI, either as a new command or in a new repository.

### 5.1. Compilation vs. Analysis

*   **Compilation**: The process of generating a final document, such as a PDF, from a source file, such as a `.tex` file. This is what we have been focused on so far.
*   **Analysis**: A new step that will be performed before compilation. This will involve a series of checks to ensure that the document is ready for compilation, including:
    *   Verifying that all required files are present.
    *   Checking that all declared artifacts have corresponding entries in `composable.toml`.
    *   Ensuring that all declared values have corresponding entries in `composable.toml`.
    *   Validating the `composable.toml` file itself.

This pre-flight checklist will provide a more robust and user-friendly experience by catching errors early and providing clear feedback to the user.