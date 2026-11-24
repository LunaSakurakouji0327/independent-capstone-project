# Genre one-hot encoding + lm() t-tests for each AI-coded dimension
# Each ";"-separated piece of the Genre cell is one genre combination,
# e.g. "fantasy, paranormal; fiction" -> combinations "fantasy, paranormal" and "fiction".

ROOT <- "C:/Users/gujia/Downloads/independent-capstone-project/Naive_LLM_analysis"   # project root; every path below is relative to it
setwd(ROOT)
if (isTRUE(getOption("knitr.in.progress"))) knitr::opts_knit$set(root.dir = ROOT)  # keep ROOT for later chunks

df <- read.csv("data/annotated/annotated_50000sample.csv", check.names = FALSE,
               stringsAsFactors = FALSE, encoding = "UTF-8")

# ---- 1. Split Genre into combinations ------------------------------------
genre_list <- lapply(strsplit(df$Genre, ";"), trimws)
genre_list <- lapply(genre_list, function(x) x[x != ""])
combos <- sort(unique(unlist(genre_list)))

# syntactic column names: "fantasy, paranormal" -> "fantasy_paranormal"
clean_name <- function(x) gsub("_+", "_", gsub("[^A-Za-z0-9]+", "_", x))
combo_vars <- clean_name(combos)
print(data.frame(combination = combos, variable = combo_vars))

# ---- 2. One-hot encoding: 1 = review's book has this combination, 0 = not
for (i in seq_along(combos)) {
  df[[combo_vars[i]]] <- as.integer(vapply(genre_list,
                                           function(g) combos[i] %in% g, logical(1)))
}
print(colSums(df[combo_vars]))   # number of reviews per combination

# Clean outcome names too: "Absence of Naive Realism_AI" -> "Absence_of_Naive_Realism_AI"
ai_cols  <- grep("_AI$", names(df), value = TRUE)
ai_vars  <- clean_name(ai_cols)
names(df)[match(ai_cols, names(df))] <- ai_vars

write.csv(df, "data/analysis_ready/annotated_50000sample_onehot.csv", row.names = FALSE, fileEncoding = "UTF-8")

# ---- 3. lm with t-tests: outcome ~ 1 + genre dummies ----------------------
rhs <- paste(c("1", combo_vars), collapse = " + ")
all_coefs <- list()
sink("results/OLS_ttest/genre_lm_results.txt")
for (y in ai_vars) {
  f <- as.formula(paste(y, "~", rhs))
  fit <- lm(f, data = df)              # rows with missing outcome are dropped
  cat("\n=====================================================\n")
  cat("Outcome:", y, "\n")
  print(summary(fit))
  ct <- as.data.frame(coef(summary(fit)))
  names(ct) <- c("estimate", "std_error", "t_value", "p_value")
  ct$term <- rownames(ct); ct$outcome <- y; ct$n <- nobs(fit)
  all_coefs[[y]] <- ct
}
sink()

res <- do.call(rbind, all_coefs)
res <- res[, c("outcome", "term", "estimate", "std_error", "t_value", "p_value", "n")]
res$sig <- cut(res$p_value, c(-Inf, .001, .01, .05, Inf), labels = c("***", "**", "*", ""))
write.csv(res, "results/OLS_ttest/genre_lm_coefficients.csv", row.names = FALSE)
print(res, digits = 3, row.names = FALSE)
