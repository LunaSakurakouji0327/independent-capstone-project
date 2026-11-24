11.15
We finished manual labelling for 100 samples. This time, I and Yuhao added our supporting logic to support our judgement.

We have several goals here:

1) Try finetuning qwen3-32b model, using human_coding_100_finished.xlsx. 80 samples in training sets and in 20 test sets. Bootstrap 500 times?

2) Adding more open-source and closed-source model. Ask LLM to generate prompt 3 and prompt 4 based on human_coding_100_finished and prompt v1. 

Select 3 LLM most aligned with human labeling results, which proves that each model is informative in judgement. Then, select other 150 sample reviews and assign four separate prompt for each model.

3) using MLA and DSL.


11.16
results

we compare qwen3-14b, gamma, sonnet, GPT-4o with human coding. We found kappa ≈ 0.4. However, we also found they violate the conditional independence. For this we are now looking forward to get four prompts in total, same definition with different examples and different phrasing.

Then, we want to compare how these four models behave in new 150 samples, at least 25 words, filter out language not in English. 

11.17
Even though we controlled text embedding, text length, and prompt, there are still irreducible correlated errors. However, the reasons could be in prompt, though we provide different examples for prompts while keeping the definition.