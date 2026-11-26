# 11. The model: WCLS and the engine's other estimators

**Summary.** Every estimate in the report and the presentation comes from the engine's weighted, centred least squares
(WCLS; Boruvka et al. 2018) fitted to one analysis frame: the outcome is regressed on the controls and on the treatment
indicator centred at a constant probability, with weights equal to that constant over the decision's own
randomization probability. With no moderators the coefficient is the marginal excursion effect, the average over the
frame's decisions of the effect of the message against the reference; with centred moderators in the effect part it
is the effect at the moderators' means plus a slope per unit of each. Standard errors are participant-clustered
sandwich estimates with the $G/(G-1)$ factor, and every estimate keeps its per-participant influence values, from which
the presentation computes the standard errors of halves, differences, joint tests and bands. Cohorts are combined by a
fixed-effect inverse-variance average. Engine versions up to 0.2.1 inverted a singular cross-product matrix without
noticing; 0.2.2 detects it and drops the redundant directions.

## Contents

- [Notation](#notation)
- [Probabilities in the model](#probabilities-in-the-model)
- [WCLS: weights, centring and the design matrix](#wcls-weights-centring-and-the-design-matrix)
- [Estimand](#estimand)
- [Moderators and centring](#moderators-and-centring)
- [Fitting and standard errors](#fitting-and-standard-errors)
- [Linear combinations from influence values](#linear-combinations-from-influence-values)
- [Tests, intervals and bands](#tests-intervals-and-bands)
- [Pooling across cohorts](#pooling-across-cohorts)
- [The collinearity fault and its fix](#the-collinearity-fault-and-its-fix)
- [DR-WCLS](#dr-wcls)
- [Who responds (question 6)](#who-responds-question-6)
- [The report's unweighted estimator](#the-reports-unweighted-estimator)
- [Which estimator each pipeline uses](#which-estimator-each-pipeline-uses)
- [Validation in the code](#validation-in-the-code)
- [Where code and documentation disagree](#where-code-and-documentation-disagree)
- [Unverified](#unverified)

## Notation

One analysis frame ([10](10-analysis-rules.md#row-filters-inside-a-comparison)) holds decisions $i = 1, \dots, n$ from
$G$ participants, one cohort, one outcome, one comparison and one period.

| Symbol | Meaning | In the code |
|---|---|---|
| $A_i \in \{0, 1, \dots, K\}$ | Arm received; 0 is the reference (no message, or the no-data version) | `AnalysisFrame.arm` |
| $Y_i$ | Outcome ([07](07-outcome-windows.md)) | `AnalysisFrame.y` |
| $X_i$ | Controls after median imputation ([08](08-controls.md)) | `AnalysisFrame.controls` |
| $Z_i$ | Moderators (none for a plain effect) | `AnalysisFrame.moderators` |
| $\pi_{i,a}$ | Published unconditional probability of arm $a$ at decision $i$ ([06](06-decisions-and-probabilities.md)) | `p_none`, `p_send`, `p_dom_*`, `p_type_*` |
| $p_{i,a}$ | The same, renormalised over the frame's arms | `AnalysisFrame.prob` |
| $\tilde p_a$ | Numerator probability, a constant per arm | `AnalysisFrame.p_tilde` |
| $g(i)$ | Participant of decision $i$ (the cluster) | `AnalysisFrame.cluster` |

[src: causal/src/ihs_causal/estimators/frame.py, AnalysisFrame; causal/src/ihs_causal/design/contrasts.py, _frame]

The presentation and report use two-arm frames throughout ($K = 1$), because every comparison they run either has two
arms or is split pairwise. Write $A_i \in \{0, 1\}$, $p_i = p_{i,1}$ and $\tilde p = \tilde p_1$ in that case.

## Probabilities in the model

**Renormalisation.** Within a frame the probabilities are those of the arms compared, rescaled to sum to one:

$$p_{i,a} = \frac{\pi_{i,a}}{\sum_{b \in \mathcal{A}} \pi_{i,b}}, \qquad a \in \mathcal{A},$$

where $\mathcal{A}$ is the frame's set of arms after small arms are dropped. The code calls this "the correct propensity
once rows are restricted to decisions that received one of those arms". For a message $k$ against no message,
$p_i = \pi_{i,k} / (\pi_{i,0} + \pi_{i,k})$. Applied.
[src: causal/src/ihs_causal/design/contrasts.py, _frame and module docstring]

**Numerator probability.** $\tilde p_a = \frac{1}{n}\sum_{i=1}^{n} p_{i,a}$, the mean of the renormalised probability
over the frame's rows: a constant, not a function of the history. Applied.
[src: causal/src/ihs_causal/estimators/frame.py, AnalysisFrame.__post_init__]

## WCLS: weights, centring and the design matrix

Applied in the report and presentation. [src: causal/src/ihs_causal/estimators/core.py, wcls]

**Weight** of decision $i$:

$$W_i = \frac{\tilde p_{A_i}}{p_{i,A_i}}, \qquad\text{two arms: } W_i = \frac{\tilde p}{p_i}\ \text{if } A_i = 1,\quad W_i = \frac{1 - \tilde p}{1 - p_i}\ \text{if } A_i = 0 .$$

This is the ratio of the fixed numerator probability to the decision's own (released, renormalised) probability of the
arm it received. Weights are not truncated, capped or stabilized further: the probability floor removes decisions
instead ([10](10-analysis-rules.md#probability-floor)). [src: core.py, wcls; contrasts.py, _frame]

**Centred treatment.** Each non-reference arm enters as $\mathbb{1}\{A_i = k\} - \tilde p_k$, centred at the constant
$\tilde p_k$, not at the decision's own probability.

**Model**, with $S_i = (1, \tilde Z_i^\top)^\top$ and $\tilde Z_i$ the centred moderators:

$$Y_i = \alpha_0 + X_i^\top \alpha + \sum_{k=1}^{K} \big(\mathbb{1}\{A_i = k\} - \tilde p_k\big)\, S_i^\top \beta_k + e_i,$$

fitted by weighted least squares with weights $W_i$. The design matrix is
$D = [\,\mathbf{1},\ X,\ (\mathbb{1}\{A = 1\} - \tilde p_1) S,\ \dots,\ (\mathbb{1}\{A = K\} - \tilde p_K) S\,]$. For each
arm the code reports the term `effect` (the coefficient on the centred indicator itself) and one term per moderator
(the coefficient on the centred indicator times that centred moderator).

Diagnostics stored with each fit: largest and mean weight, Kish's effective sample as a share of rows
$\big(\sum W_i\big)^2 / \big(n \sum W_i^2\big)$, the smallest observed probability, the condition number and the number of
directions dropped ([below](#the-collinearity-fault-and-its-fix)). [src: core.py, wcls, _weight_diagnostics]

## Estimand

**What the coefficient estimates.** Let
$\tau_k(H_i) = E\big[Y_i(k) - Y_i(0) \mid H_i\big]$ be the excursion effect at decision $i$: the expected difference in
the proximal outcome between giving arm $k$ and giving the reference at that decision, with everything before it as it
happened. For two arms, the weights and the constant centring give, for any function $f$ of the history,

$$E\big[W_i (A_i - \tilde p) f(H_i) \mid H_i\big] = 0, \qquad E\big[W_i (A_i - \tilde p)^2 \mid H_i\big] = \tilde p(1 - \tilde p), \qquad E\big[W_i (A_i - \tilde p) Y_i \mid H_i\big] = \tilde p(1 - \tilde p)\, \tau(H_i),$$

so the controls drop out of the equations for $\beta$ and

$$\beta = \Big(\sum_i E\big[S_i S_i^\top\big]\Big)^{-1} \sum_i E\big[S_i\, \tau(H_i)\big].$$

[src: Boruvka et al. 2018, as cited in causal/src/ihs_causal/estimators/core.py, module docstring; the three
identities are derived here from the weights and the centring in `wcls`]

- **No moderators** ($S_i = 1$): $\beta$ is the average of $\tau(H_i)$ over the frame's decisions, the marginal
  excursion effect. Every decision counts equally because $\tilde p(1 - \tilde p)$ is the same for all of them.
  The engine's docstring writes this as $\beta_k(S) = E[Y(k) - Y(0) \mid S]$ under the numerator probabilities.
  Applied. [src: core.py, module docstring]
- **With centred moderators:** $S^\top \beta$ is the least-squares projection of $\tau$ on $(1, \tilde Z)$. The
  `effect` term is the effect at the moderators' means among the frame's decisions, and each moderator term is the
  change in the effect per unit of that moderator, holding the others fixed, under a linear form. Applied.
  [src: core.py, module docstring; contrasts.py, _frame (centring)]
- **The controls do not change the estimand**, only precision, as long as the probabilities are the ones the decisions
  were randomized with. [derived from the first identity]
- **Which decisions are averaged over** [derived here; not stated in the code or docs]:
  - Only the frame's decisions: in the analysis set, with the outcome recorded, with published probabilities at or above
    the floor, and with any moderator recorded. If whether the outcome is recorded depends on the message, the average
    is over a set the message helped choose; the code does not adjust for that.
  - The frame keeps only decisions that received one of the two compared arms, a selection that depends on the history.
    Working the identities through with that selection, a decision of the analysis set counts in proportion to
    $\pi_{i,0} + \pi_{i,k}$, the chance that it fell in the compared pair; the frame over-represents histories where the
    pair was likely. For any message against none this is 1 for every decision. For a 2025 domain comparison it is 1 within that
    domain's weeks. For 2024 domain comparisons and for strategy comparisons it varies with the history, so the
    "marginal" effect leans toward decisions where that domain or strategy was likely.
  - In 2025, domain and strategy comparisons average over the domain's weeks only.
- **Multi-arm frames** (`positivity: joint`, not used by the report or presentation): the same argument with the
  multinomial covariance of the centred indicators gives $\beta_k$ as the projection of $\tau_k$ on $S$ for each arm.
  [derived]

## Moderators and centring

- **Centring.** Moderators are centred at their mean over the frame's rows, after every row filter:
  $\tilde Z_i = Z_i - \bar Z$. They are not scaled. The mean is recomputed in every frame (cohort, period, comparison, arm). Applied.
  [src: causal/src/ihs_causal/design/contrasts.py, _frame (`mods - mods.mean(axis=0)`)]
- **Complete cases.** A frame with moderators keeps only decisions where each is recorded, so median imputation never
  touches a moderator. [src: contrasts.py, _frame]
- **Main effects.** The engine puts a moderator in the effect part only; the report and presentation also list it among
  the controls ([08](08-controls.md#moderators-as-controls)).
- **0/1 indicators** (presentation): centring an indicator $u$ with share $\bar u$ in the upper half makes the `effect`
  term the effect at $u = \bar u$; the halves are recovered as linear combinations ([next section](#linear-combinations-from-influence-values)).
- **Question 6** standardizes each moderator over its own complete cases, which gives slopes per SD
  ([below](#who-responds-question-6)). [src: causal/src/ihs_causal/estimators/hetero.py, drwcls_hetero]

## Fitting and standard errors

Every estimator in the engine reduces to one weighted least-squares routine. Applied.
[src: causal/src/ihs_causal/estimators/wls.py, wls_cluster]

With $D$ the design matrix, $\mathbf{W} = \operatorname{diag}(W_i)$ and residuals $\hat e_i = Y_i - D_i^\top \hat\theta$:

$$\hat\theta = (D^\top \mathbf{W} D)^{-1} D^\top \mathbf{W} Y,$$

$$\hat\psi_g = (D^\top \mathbf{W} D)^{-1} \sum_{i:\, g(i) = g} W_i\, D_i\, \hat e_i \qquad (g = 1, \dots, G),$$

$$\widehat{\operatorname{Var}}(\hat\theta) = \frac{G}{G - 1} \sum_{g=1}^{G} \hat\psi_g \hat\psi_g^\top .$$

- $\hat\psi_g$ is participant $g$'s influence value: $\hat\theta - \theta \approx \sum_g \hat\psi_g$. Every estimate is
  stored with its vector of $\hat\psi_g$ for the term. [src: wls.py, WLSResult; core.py, _collect]
- **Clusters are participants**; $G$ is the number of participants in the frame. The only small-sample correction is
  the factor $G/(G-1)$. [src: wls.py, wls_cluster]
- **The numerator probabilities and the moderator means are estimated from the frame but treated as fixed** in the
  variance. [derived from the code: neither enters the sandwich]
- Standard error, $z = \hat\beta / \widehat{SE}$, two-sided normal p-value and the 95% interval
  $\hat\beta \pm 1.959964\, \widehat{SE}$. [src: causal/src/ihs_causal/estimators/inference.py, summarize]

## Linear combinations from influence values

The presentation never refits to get a half or a difference. It combines coefficients and their influence values:

$$\widehat{SE}\big(c^\top \hat\beta\big) = \sqrt{\frac{G}{G-1} \sum_{g=1}^{G} \big(c^\top \hat\psi_g\big)^2 }.$$

Applied (presentation). [src: <vault>/Presentation Plots/pipeline/screen_fit.py, halves, quarters]

- **Figure 1b, one moderator.** The model has the half indicator $u$ as control and moderator, so the effect part is
  $b_0 + \tilde u\, b_1$ with $\tilde u = u - \bar u$. With $u_0 = -\bar u$ and $u_1 = 1 - \bar u$ the centred values of
  the lower and upper halves:

  $$\text{lower} = b_0 + u_0 b_1, \qquad \text{upper} = b_0 + u_1 b_1, \qquad \text{difference} = (u_1 - u_0) b_1 = b_1 .$$

  [src: screen_fit.py, halves]
- **Figure 1b, two moderators** (daytime sleep and warmth): indicators $a$, $b$ and their product, all centred, as
  controls and moderators. The effect in group $(a, b)$ is
  $b_{\text{effect}} + \tilde a\, b_a + \tilde b\, b_b + \widetilde{ab}\, b_{ab}$; the rows are differences of two
  groups, or the difference of two such gaps (the interaction). [src: screen_fit.py, quarters]
- **Report display levels are not computed this way:** each level is a separate fit on its subset, with the measure
  left out of the controls. [src: report/ihs_report/moderation.py, fit_cohort]

## Tests, intervals and bands

| What | How | Used by | Source |
|---|---|---|---|
| Pointwise 95% interval | $\hat\beta \pm 1.96\,\widehat{SE}$, normal p-value | All | `inference.py`, `summarize`; `report/ihs_report/pooling.py`, `two_sided_p` |
| Simultaneous intervals for a family | Multiplier bootstrap: $\xi_g \sim N(0, 1)$, 2,000 draws, seed 20261117; critical value $c$ = 95% quantile of $\max_j \lvert \sum_g \xi_g \hat\psi_{gj} \rvert / \widehat{SE}_j$; interval $\hat\beta_j \pm c\, \widehat{SE}_j$ | Engine app | `inference.py`, `simultaneous_critical_value`; `causal/src/ihs_causal/results.py`, `add_simultaneous` |
| All moderators together (figure 2) | Wald $T = \hat b^\top \hat V^{+} \hat b$ against $\chi^2$ with as many degrees of freedom as terms, $\hat V = \frac{G}{G-1} \Psi^\top \Psi$ from the influence matrix $\Psi$, $^{+}$ the pseudo-inverse | Presentation | `joint_fit.py`, `fit_cohort`, `wald` |
| Band along a cumulative curve | Correlation $R$ of the cutoff estimates from their influence values (participants missing at a cutoff count as 0); $c$ = 95% quantile of $\max_j \lvert Z_j \rvert$, $Z \sim N(0, R)$, 10,000 draws, seed 20261125; band $\hat\beta_j \pm c\, \widehat{SE}_j$ over the cutoffs shown | Presentation | `cumulative_fit.py`, `crit`, `curves` |
| Benjamini-Hochberg q-values | Over a family of p-values | Report; engine question 6 | `report/ihs_report/pooling.py`, `benjamini_hochberg`; `results.py`, `add_bh` |

Families and q-value scopes: [10](10-analysis-rules.md#multiplicity).

## Pooling across cohorts

Fixed-effect inverse-variance average of the cohort estimates $\hat\beta_c$ with standard errors $s_c$:

$$w_c = \frac{1}{s_c^2}, \qquad \hat\beta_{\text{pool}} = \frac{\sum_c w_c \hat\beta_c}{\sum_c w_c}, \qquad
\widehat{SE}_{\text{pool}} = \Big(\sum_c w_c\Big)^{-1/2}, \qquad z = \hat\beta_{\text{pool}} / \widehat{SE}_{\text{pool}}.$$

Applied (report and presentation). [src: report/ihs_report/pooling.py, pool]

- **Also computed by the report:** the equal-weight mean, $\bar\beta = \frac{1}{C}\sum_c \hat\beta_c$ with
  $\widehat{SE} = \sqrt{\sum_c s_c^2}/C$, and the cohort difference $\hat\beta_{2025} - \hat\beta_{2024}$ with
  $\widehat{SE} = \sqrt{s_{2024}^2 + s_{2025}^2}$ and its $z$, reported as `diff_z`. [src: pooling.py, pool;
  report/ihs_report/moderation.py, pooled_rows]
- **The cohorts are treated as independent.** [assumed by the formulas; the cohorts are different intern classes]
- **Figure 2's joint test pooled:** $\hat V_p = \big(\sum_c \hat V_c^{+}\big)^{+}$ and
  $\hat b_p = \hat V_p \sum_c \hat V_c^{+} \hat b_c$ on the terms both cohorts have. [src: joint_fit.py, finish]
- **Cumulative curves pooled:** inverse-variance at each cutoff; the pooled influence values are
  $\sum_c (w_c / \sum_{c'} w_{c'})\, \hat\psi_{g,c}$, with participants of the two cohorts kept apart, and they feed the
  pooled band. [src: cumulative_fit.py, curves]
- When a pooled row exists in each pipeline: [10](10-analysis-rules.md#pooling-the-cohorts).

## The collinearity fault and its fix

**Fault, engine 0.2.1 and earlier.** Superseded. `wls_cluster` inverted $B = D^\top \mathbf{W} D$ with
`np.linalg.inv` and fell back to the pseudo-inverse only when that raised an error. When some columns of $D$ are an
exact, or numerically exact, combination of others on the rows of a fit, $B$ is singular but `inv` often raises
nothing and returns noise. The coefficients of the other columns usually stayed roughly right, their sandwich standard
errors were meaningless, and in the worst cases the estimates were too. Found 2026-11-23.
[src: causal/src/ihs_causal/estimators/wls.py, module docstring; `git diff` of wls.py against HEAD; report/README.md,
"A fault in the engine, fixed in engine 0.2.2"]

**Where it bit** (no estimates here): the report's port of the audit's long-history weather analysis, where the
components of the long-history set were collinear on some subsets of days, affecting single-cohort level standard
errors and the pooled levels built from them; and the audit's study-time interactions, where study time over 30 days
sat beside the control `t`. In the weather analysis every overall effect and moderation test was unaffected; the
audit's study-time interactions (moderation tests) are unreliable, while its effects by period were separate fits and
sound. [src: report/README.md, "A fault in the engine"; project memory note of 2026-11-23]

**Fix, engine 0.2.2** (working tree, uncommitted; Drew asked for it on 2026-11-23). Applied.
[src: causal/src/ihs_causal/estimators/wls.py, _inverse, wls_cluster; causal/tests/test_collinear_controls.py]

1. Scale $B$ to unit diagonal: $\Delta = \operatorname{diag}(B)^{1/2}$ (a zero entry replaced by 1),
   $\tilde B = \Delta^{-1} B \Delta^{-1} = V \Lambda V^\top$.
2. Directions with $\lambda_j \le 10^{-10} \lambda_{\max}$ (`COLLINEAR_TOL`, a condition number above $10^{10}$) are
   treated as zero. The condition number $\lambda_{\max} / \lambda_{\min}$ is recorded.
3. **None small:** the plain inverse, exactly as before.
4. **Some small:** the pseudo-inverse of the scaled matrix over the kept directions,
   $B^{+} = \Delta^{-1} V_{\text{kept}} \Lambda_{\text{kept}}^{-1} V_{\text{kept}}^\top \Delta^{-1}$. The coefficients
   and standard errors of identified columns are then those of the model without the redundant columns.
5. **Identification:** column $c$ is identified when $\max_{j\ \text{dropped}} \lvert V_{cj} \rvert < 10^{-6}$
   (`IDENTIFIED_TOL`). A column that is not identified gets a missing coefficient, influence and variance.
6. WCLS records `condition_number` and `collinear_directions_dropped`; the report counts fits where directions were
   dropped (`report/ihs_report/estimate.py`, `STABILISED`).

The fix applies to every engine estimator, since all call `wls_cluster`. The report's own unweighted estimator always
used the pseudo-inverse. [src: core.py; report/ihs_report/estimate.py, least_squares]

## DR-WCLS

`drwcls`, the engine's default estimator (`estimator.name: drwcls` in the defaults). Applied in the engine's standing
analyses; not used by the report or presentation. [src: causal/src/ihs_causal/defaults.yaml; causal/src/ihs_causal/
estimators/core.py, drwcls; causal/src/ihs_causal/estimators/nuisance.py]

1. **Outcome model per arm**, cross-fitted by participant: participants are split into 5 folds (seed 20261117); for
   each fold and arm $a$, a learner is fitted on the other folds' decisions that received $a$ and predicts
   $\hat\mu_a(H_i)$ for the held-out decisions. Features are the `nuisance` variables, median-filled with missing flags
   ([08](08-controls.md#outcome-model-variables-dr-wcls)).
2. **Learner:** ridge regression on standardized features, the penalty chosen by generalized cross-validation over
   $\lambda \in n \times \{10^{-6}, \dots, 10^{1}\}$ (29 values, log-spaced); an arm with fewer than 50 training rows
   uses its mean (`mean` learner). [src: nuisance.py, RidgeGCV, crossfit_arm_means]
3. **Pseudo-outcome** for arm $k$:

   $$\tilde Y_{i,k} = \Big(\frac{\mathbb{1}\{A_i = k\}}{p_{i,k}} - \frac{\mathbb{1}\{A_i = 0\}}{p_{i,0}}\Big)\big(Y_i - \hat\mu_{A_i}(H_i)\big) + \hat\mu_k(H_i) - \hat\mu_0(H_i).$$

4. **Final regression**, unweighted: $\tilde Y_{i,k}$ on $S_i$, with the same clustered sandwich.

The estimand is the same as WCLS's with equal decision weights; with known probabilities the outcome model reduces
variance but cannot bias the effect. Nuisance-estimation error is ignored in the variance, justified in the code by the
known probabilities and cross-fitting. [src: core.py, module docstring; causal/docs/DESIGN.md, "Estimators"]
Out-of-fold $R^2$ per arm is stored as a diagnostic.

## Who responds (question 6)

`drwcls_hetero`. Applied in the engine's question-6 analyses (`causal/config/q6_*.yaml`); not used by the report or
presentation. [src: causal/src/ihs_causal/estimators/hetero.py, drwcls_hetero; causal/config/q6_2024.yaml]

- **Moderation:** the DR-WCLS pseudo-outcome regressed on $(1, z)$ for each characteristic alone, $z$ standardized over
  the decisions where it is recorded; slope per SD; not adjusted for other characteristics. Skipped below 100 recorded
  decisions or with one value.
- **Variation between people:** split-half covariance. Each participant's study weeks alternate between two halves
  ($\lfloor t/7 \rfloor \bmod 2$); the covariance across participants of the two half-means estimates $\tau^2$, the
  variance of true person-level effects. A participant needs 5 decisions in each half; 20 participants are needed.
  Participant-bootstrap interval (400 draws); sign-flip p-value (2,000 draws). A REML random-effects model with
  per-person variances is reported alongside; a participant needs 10 decisions.
- **Explained by baseline:** the share of $\tau^2$ removed by baseline traits, the trait model fitted on one half and
  applied to the other.
- Empirical-Bayes shrunken person effects stay in the engine's `work/` folder.

## The report's unweighted estimator

Least squares of $Y$ on $[1, X, A - p_i]$ with no weights, $p_i$ the decision's own renormalised probability of the
message. Its estimand weights each decision by $p_i(1 - p_i)$, so decisions randomized near 50/50 count most. Used only
in the report's "other levers" check. Option, not default. [src: report/ihs_report/estimate.py, unweighted_rows,
least_squares; report/ihs_report/analyses/other_levers.py]

## Which estimator each pipeline uses

| Pipeline | Estimator | Controls | Source |
|---|---|---|---|
| Report (every effect and moderator analysis) | `wcls` (`engine.estimator.name` in the settings; the outcome model is switched off) | standard | `report/config/analysis.yaml`; `report/ihs_report/context.py`, `Context.spec` |
| Presentation (figures 1b and 2, cumulative curves) | `wcls`, called directly as `ESTIMATORS.get("wcls")` | standard plus split indicators | `<vault>/Presentation Plots/pipeline/screen_fit.py`, `WCLS` |
| Engine standing analyses, questions 1 to 5 | `drwcls` | `nuisance` list | `causal/src/ihs_causal/defaults.yaml`; `causal/config/primary_*.yaml` |
| Engine question 6 | `drwcls_hetero` | `nuisance` list | `causal/config/q6_*.yaml` |
| Engine `july_december_*.yaml` (uncommitted, not standing) | `wcls` | engine five | `causal/config/july_december_2024.yaml` |
| Report "other levers" | `wcls` and the unweighted estimator | standard | `report/ihs_report/analyses/other_levers.py` |

## Validation in the code

- Simulated trials with known effects: both estimators recover marginal effects and a moderator slope, WCLS intervals
  cover at about 95%, DR-WCLS is at least as precise, simultaneous critical values lie above 1.96.
  [src: causal/docs/DESIGN.md, "Validation"; causal/tests/test_estimators.py]
- Collinear controls: `causal/tests/test_collinear_controls.py` (new, uncommitted).
- Fake files with a built-in step effect, recovered end to end by the engine and by the report.
  [src: causal/docs/DESIGN.md, "Validation"; report/README.md, "Getting the same numbers"]

## Where code and documentation disagree

Code wins in every case below.

1. **Results stored by the engine app before 0.2.2.** `report/README.md` says they "are not recomputed automatically
   (its store is keyed on the input files)". In the working tree the store's key also includes the outcome-rule
   version (`outcome_rules: window-stats-v5`), so runs stored before that key existed no longer match and are flagged as
   made from older data; `ihs-causal reproduce` and `refresh` redo them, under the fixed estimator. The key holds no
   package or estimator version, so a run stored with the new key but before the `wls.py` fix (both changes are
   uncommitted in the same working tree) would still match and not be redone; whether any such run exists is
   unverified.
   [src: causal/src/ihs_causal/workspace.py, Workspace.result_inputs; causal/src/ihs_causal/results.py, inputs_match;
   causal/src/ihs_causal/runner.py, pending_specs]
2. **Pooling equals a stacked model.** `report/ihs_report/pooling.py` says the inverse-variance average "equals one
   stacked model with cohort-specific intercept and controls and a single message term". For weighted least squares
   with sandwich variances that holds only approximately: a stacked fit weights each cohort by its model-based
   information, not by the inverse of its sandwich variance. Not checked numerically here.
3. **Multiplier draws and the small-sample factor.** The engine's simultaneous critical value divides influence sums
   that lack the $G/(G-1)$ factor by standard errors that include it, so the critical value is smaller by about
   $\sqrt{(G-1)/G}$. Negligible with hundreds of participants. [derived from inference.py, simultaneous_critical_value,
   and wls.py, wls_cluster]

## Unverified

- The Boruvka et al. (2018) result is cited, not re-derived in full; the decision-weight statement for frames selected
  on the compared pair is derived here and is not in the code or docs.
- Whether the recording of each outcome depends on the message, in each cohort (it matters for the estimand above). The audit of 2026-11-20 looked at this for some outcomes; its numbers are results and are not
  repeated here.
