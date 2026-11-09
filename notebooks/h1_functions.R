# ---- H1 helpers --------------------------------------------------------------

# Keep one row per decision.
#   device = "pooled": combined Healthkit row for Apple users (watch/phone rows dropped);
#            if a participant has data from several device families, keep the one with
#            the most hours of step data over the study.
#   device = "Fitbit" / "Garmin" / "Healthkit" / ...: only that device's rows.
select_device_rows <- function(data, device = "pooled") {
  d <- data %>% filter(has_decision)
  if (device == "pooled") {
    d <- d %>% filter(!device_type %in% c("HealthkitWatch", "HealthkitPhone"))
    keep <- d %>%
      group_by(participant_id, device_type) %>%
      summarise(cov = sum(steps_n_post, na.rm = TRUE), .groups = "drop") %>%
      group_by(participant_id) %>%
      slice_max(cov, n = 1, with_ties = FALSE) %>%
      ungroup() %>%
      select(participant_id, device_type)
    d <- d %>% semi_join(keep, by = c("participant_id", "device_type"))
  } else {
    d <- d %>% filter(device_type == device)
  }
  stopifnot(!anyDuplicated(d$decision_id))
  d
}

# Outcome and history variables shared by all domains.
#   Sums over windows with too little data or an unusual length are set to NA.
derive_variables <- function(d, min_cov = 0.75, span_range = c(20, 28)) {
  ok_span <- function(s) !is.na(s) & s >= span_range[1] & s <= span_range[2]
  for (w in c("pre", "post")) {
    span <- d[[paste0("span_h_", w)]]
    for (s in c("steps", "sleep_minutes")) {
      v <- paste0(s, "_", w)
      n <- d[[paste0(s, "_n_", w)]]
      d[[v]] <- ifelse(ok_span(span) & !is.na(n) & n >= min_cov * span, d[[v]], NA)
    }
    d[[paste0("Mood_", w)]] <- ifelse(ok_span(span), d[[paste0("Mood_", w)]], NA)
    d[[paste0("log_steps_", w)]] <- log1p(d[[paste0("steps_", w)]])
  }
  d$dow <- as.integer(format(as.POSIXct(d$decision_time_utc, tz = "UTC"), "%u"))  # 1 = Monday (UTC)
  d
}

# Treatment, randomization probability and analysis rows for one contrast.
#   domain = "any": any message vs no message, P(A = 1) = p_send.
#   domain = "mood"/"steps"/"sleep": a message of that domain vs no message; decisions
#   with a message of another domain are dropped, so
#   P(A = 1 | H_t, kept) = p_send * p_domain / (p_send * p_domain + p_no_send).
code_treatment <- function(d, domain, metric_values) {
  if (domain == "any") {
    d$A <- d$action_id
    d$prob <- d$p_send
  } else {
    m <- metric_values[[domain]]
    d <- d %>% filter(action_id == 0 | message_metric == m)
    p_dom <- d[[paste0("p_", domain)]]
    d$A <- d$action_id
    d$prob <- d$p_send * p_dom / (d$p_send * p_dom + d$p_no_send)
  }
  stopifnot(all(d$A %in% c(0, 1)), all(d$prob > 0 & d$prob < 1))
  d
}

# Median-impute history variables and add missingness indicators (the nuisance
# learners cannot take NA). Uses only history, never the outcome.
impute_history <- function(d, Ht) {
  out <- Ht
  for (v in Ht) {
    miss <- is.na(d[[v]])
    if (any(miss)) {
      d[[paste0(v, "_miss")]] <- as.integer(miss)
      d[[v]][miss] <- median(d[[v]], na.rm = TRUE)
      out <- c(out, paste0(v, "_miss"))
    }
  }
  list(data = d, Ht = out)
}

# Cross-fitted nuisance models from MRTpostInfLASSO, then the DR pseudo-outcome with
# the known randomization probability and a constant reference probability
# p_tilde = mean(prob) (S_t is empty for the marginal effect).
PRED_COLS <- list(
  RandomForest     = c("gt_pred_rf", "gtAt1_pred_rf", "gtAt0_pred_rf"),
  GradientBoosting = c("gt_pred_gbm", "gtAt1_pred_gbm", "gtAt0_pred_gbm"),
  CVLASSO          = c("lasso.pred.gt", "lasso.pred.gtAt1", "lasso.pred.gtAt0")
)

# Lean cross-fitting with ranger: same outcome model as the package
# (Y ~ Ht + A + Ht:A, participants split into folds), but folds run one at a time,
# only the outcome model is fit (treatment probabilities are known), and forest
# size is controllable, so memory stays bounded.
crossfit_rf_lean <- function(d, Ht, outcome, fold, num_threads, seed,
                             num_trees = 300, min_node_size = 50) {
  # split participants into folds (same scheme as the package's internal split_data)
  set.seed(seed)
  ids <- sample(unique(d$participant_id))
  folds <- split(ids, rep(seq_len(fold), length.out = length(ids)))
  d <- as.data.frame(d)
  add_inter <- function(x) {
    for (v in Ht) x[[paste0(v, ".A")]] <- x[[v]] * x$A
    x
  }
  feats <- c(Ht, "A", paste0(Ht, ".A"))
  f <- as.formula(paste(outcome, "~", paste(feats, collapse = " + ")))
  out <- vector("list", length(folds))
  for (k in seq_along(folds)) {
    test <- d$participant_id %in% folds[[k]]
    rf <- ranger::ranger(f, data = add_inter(d[!test, c(outcome, Ht, "A")]),
                         num.trees = num_trees, min.node.size = min_node_size,
                         num.threads = num_threads, seed = seed + k,
                         write.forest = TRUE, verbose = FALSE)
    te <- d[test, ]
    te1 <- te; te1$A <- 1
    te0 <- te; te0$A <- 0
    te$gt_pred_rf    <- predict(rf, add_inter(te[,  c(Ht, "A")]), num.threads = num_threads)$predictions
    te$gtAt1_pred_rf <- predict(rf, add_inter(te1[, c(Ht, "A")]), num.threads = num_threads)$predictions
    te$gtAt0_pred_rf <- predict(rf, add_inter(te0[, c(Ht, "A")]), num.threads = num_threads)$predictions
    out[[k]] <- te
    rm(rf); gc(verbose = FALSE)
  }
  do.call(rbind, out)
}

dr_pseudo_outcomes <- function(d, Ht, outcome, method, fold, core_num, seed) {
  if (method == "RandomForestLean") {
    ps <- crossfit_rf_lean(d, Ht, outcome, fold, num_threads = core_num, seed = seed)
    return(finish_pseudo(ps, d, outcome, PRED_COLS[["RandomForest"]]))
  }
  gen <- switch(method,
    RandomForest     = pseudo_outcome_generator_rf_v2,
    GradientBoosting = pseudo_outcome_generator_gbm,
    CVLASSO          = pseudo_outcome_generator_CVlasso)
  # The package also fits E[A | S_t] and needs a non-empty S_t (two columns for
  # CVLASSO). That estimate is not used: it is replaced below by the constant p_tilde.
  ps <- gen(fold = fold, ID = "participant_id", data = as.data.frame(d),
            Ht = Ht, St = Ht[1:2], At = "A", prob = "prob", outcome = outcome,
            core_num = core_num, master_seed = seed)
  finish_pseudo(ps, d, outcome, PRED_COLS[[method]])
}

finish_pseudo <- function(ps, d, outcome, pc) {
  A <- ps$A; p <- ps$prob
  p_tilde <- mean(d$prob)
  W <- ifelse(A == 1, p_tilde / p, (1 - p_tilde) / (1 - p))
  ps$p_tilde <- p_tilde
  ps$W <- W
  ps$yDR <- W * (A - p_tilde) * (ps[[outcome]] - ps[[pc[1]]]) / (p_tilde * (1 - p_tilde)) +
    (ps[[pc[2]]] - ps[[pc[3]]])
  ps %>% arrange(participant_id, t)
}

# Marginal effect: weighted regression of yDR on an intercept, sandwich SE clustered
# by participant (as in the package's GEE step).
fit_marginal <- function(ps, level = 0.95) {
  ps <- ps %>% arrange(participant_id, t)
  wt <- ps$p_tilde * (1 - ps$p_tilde)
  fit <- geepack::geeglm(yDR ~ 1, data = ps, weights = wt,
                         id = factor(participant_id, levels = unique(participant_id)),
                         corstr = "independence")
  tidy_gee(fit, "(Intercept)", level)
}

# WCLS check: linear control model, centered treatment, weights W.
fit_wcls <- function(d, Ht_lin, outcome, level = 0.95) {
  d <- d %>% arrange(participant_id, t)
  p_tilde <- mean(d$prob)
  d$A_c <- d$A - p_tilde
  d$W <- ifelse(d$A == 1, p_tilde / d$prob, (1 - p_tilde) / (1 - d$prob))
  f <- as.formula(paste(outcome, "~", paste(c(Ht_lin, "A_c"), collapse = " + ")))
  fit <- geepack::geeglm(f, data = d, weights = W,
                         id = factor(participant_id, levels = unique(participant_id)),
                         corstr = "independence")
  tidy_gee(fit, "A_c", level)
}

tidy_gee <- function(fit, term, level) {
  s <- summary(fit)$coefficients
  est <- s[term, "Estimate"]; se <- s[term, "Std.err"]
  z <- qnorm(1 - (1 - level) / 2)
  tibble(estimate = est, se = se, lower = est - z * se, upper = est + z * se,
         p_value = 2 * pnorm(-abs(est / se)))
}

# One H1 analysis: contrast for `domain`, outcome `outcome`.
run_h1 <- function(data, domain, outcome, Ht, Ht_lin, metric_values,
                   device = "pooled", method = "RandomForest",
                   fold = 5, core_num = 4, seed = 2024, min_participants = 20) {
  d <- data %>%
    select_device_rows(device) %>%
    code_treatment(domain, metric_values)
  n_all <- nrow(d)
  d <- d %>% filter(!is.na(.data[[outcome]]))
  n_id <- n_distinct(d$participant_id)
  if (n_id < max(fold, min_participants)) {
    message(sprintf("skipping %s / %s / %s: %d participants with outcome data (need %d)",
                    domain, outcome, device, n_id, max(fold, min_participants)))
    return(list(results = tibble(domain = domain, outcome = outcome, device = device,
                                 n_participants = n_id, n_decisions = nrow(d),
                                 estimator = NA_character_, estimate = NA_real_, se = NA_real_,
                                 lower = NA_real_, upper = NA_real_, p_value = NA_real_),
                pseudo = NULL))
  }
  imp <- impute_history(d, Ht)
  d <- imp$data

  ps <- dr_pseudo_outcomes(d, imp$Ht, outcome, method, fold, core_num, seed)
  sd_y <- sd(d[[outcome]][d$A == 0])

  res <- bind_rows(
    fit_marginal(ps) %>% mutate(estimator = paste0("DR-WCLS (", method, ")")),
    fit_wcls(d, Ht_lin, outcome) %>% mutate(estimator = "WCLS (linear control)")
  ) %>%
    mutate(domain = domain, outcome = outcome, device = device,
           n_participants = n_distinct(d$participant_id),
           n_decisions = nrow(d), n_missing_outcome = n_all - nrow(d),
           p_treated = mean(d$A), p_tilde = mean(d$prob),
           std_effect = estimate / sd_y,
           .before = 1)
  list(results = res, pseudo = ps)
}
