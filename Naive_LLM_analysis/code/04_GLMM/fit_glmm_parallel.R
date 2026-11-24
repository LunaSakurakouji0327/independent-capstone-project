# Fit the 7 random-intercept models of genre_glmer_random_intercepts.qmd in parallel.
# Data preparation and the model formulas are taken from the qmd itself, so they are identical.
#
#   Rscript code/04_GLMM/fit_glmm_parallel.R 0     # nAGQ = 0  (fast)
#   Rscript code/04_GLMM/fit_glmm_parallel.R 1     # nAGQ = 1  (Laplace; uses nAGQ = 0 fits as start values)
#
# Results: cache/models_nagq0/g<k>_nagq0.rds and cache/models_nagq1/g<k>_nagq1.rds  (the qmd loads these instead of refitting)

setwd("C:/Users/gujia/Downloads/independent-capstone-project/Naive_LLM_analysis")
nagq <- as.integer(commandArgs(trailingOnly = TRUE)[1])
if (is.na(nagq)) nagq <- 0

code_file <- file.path(tempdir(), "glmm_qmd_code.R")
knitr::purl("code/04_GLMM/genre_glmer_random_intercepts.qmd", output = code_file, quiet = TRUE)
exprs <- parse(code_file, keep.source = FALSE)

is_model <- function(e) is.call(e) && identical(e[[1]], as.name("<-")) &&
  grepl("^g[1-7]$", deparse(e[[2]])) && is.call(e[[3]]) && identical(e[[3]][[1]], as.name("fit_glmm"))
model_idx <- which(vapply(exprs, is_model, logical(1)))
prep <- exprs[seq_len(min(model_idx) - 1)]        # everything before the first model
model_exprs <- exprs[model_idx]
names(model_exprs) <- vapply(model_exprs, function(e) deparse(e[[2]]), "")

out_dir <- if (nagq == 0) "cache/models_nagq0" else "cache/models_nagq1"
todo <- names(model_exprs)[!file.exists(sprintf("%s/%s_nagq%d.rds", out_dir, names(model_exprs), nagq))]
cat("nAGQ =", nagq, "| models to fit:", paste(todo, collapse = ", "), "\n")
if (!length(todo)) quit(save = "no")

cl <- parallel::makeCluster(length(todo))         # one core per model
on.exit(parallel::stopCluster(cl))
parallel::clusterExport(cl, c("prep", "nagq"))
parallel::clusterEvalQ(cl, {
  setwd("C:/Users/gujia/Downloads/independent-capstone-project/Naive_LLM_analysis")
  sink(nullfile())
  for (e in prep) eval(e, envir = globalenv())    # load data, one-hot, define fit_glmm()
  sink()
  NAGQ <<- nagq
  NULL
})

t0 <- Sys.time()
res <- parallel::parLapplyLB(cl, model_exprs[todo], function(e) {
  t <- system.time(m <- eval(e, envir = globalenv()))[["elapsed"]]
  conv <- m@optinfo$conv$lme4$messages
  sprintf("%s: %.1f min %s", deparse(e[[2]]), t / 60,
          if (is.null(conv)) "(converged OK)" else paste("| warning:", paste(conv, collapse = "; ")))
})
cat(unlist(res), sep = "\n")
cat(sprintf("All done in %.1f min\n", as.numeric(difftime(Sys.time(), t0, units = "mins"))))
