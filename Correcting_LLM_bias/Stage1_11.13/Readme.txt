Hi!
This is a recap for what we have done so far before 11/15
Basically, this is a project of LLM automatic annotation.
Over the last half year, we spent much time on manual labeling to create the validation set.
Dr. Buttrick's goal is to ask LLM to mimic our human responses so that LLM can help us label automatically.

However, using single LLM to annotate might lead to decreased confidence interval even if the accuracy of LLM annotation is high (based on human coding). You will find it is hard to label some book reviews because it is in the grey area. Moreover, this might lead to biased parameter estimate if we solely rely on LLM annotation, which is called Naive LLM labeling.

There are plenty of ways to reduce the bias of parameter estimate. Generally, Jiangran Gu and Yuhao Wang are right now working on Design-Based Supervised Learning (DSL) and Debiased Inference with Multiple Imperfect Measures (DMM). We also aim to using Maximum Likelihood Adjustment (MLA) to see how NLP annotation can be corrected to best fit the parameter estimate with less bias.

Please review DSL, DMM, MLA Just skip the math part and read the prerequisite.

About experiments in this folder.

we used chatgpt 4o mini to run labelling on 100 samples. Unfortunately, we did not cover the AI answer before human labelling, which means AI labelling might bias us and lead to high accuracy.

All specific reports are in the report docx.

This time, we only filter >25 words book reviews

Basically, even if we use the same prompt, there are plenty of differences in labelling results across different models.

v1 is the original prompt we are using
v2 is the original prompt + specific examples. We assume that models will have more specific baselines, and they did. 

