# 2026-09-23
prompts = {
    "Absence of Naive Realism": """
Naive Realism determines whether the reviewer recognizes that other people may reasonably hold a different opinion or interpretation.
Code as 1
Code as 1 when the review clearly acknowledges that:
another reader may think, feel, or judge differently;
more than one interpretation or evaluation may be reasonable;
the book may affect different readers in different ways.
The acknowledgment may be explicit or clearly conveyed by the overall meaning.
Code as 0
Code as 0 when the review does not clearly recognize a reasonable difference in opinion or interpretation.
Personal wording, preferences, emotions, uncertainty, background information, or references to popularity are not sufficient by themselves.
A score of 0 does not mean the reviewer claims to be objectively correct. It only means that differing viewpoints are not clearly acknowledged.
When the evidence is ambiguous, code as 0.

RETURN ONLY:
0 or 1

Review:
{text}
""",
    "Theme": """
Theme distinguishes between a Surface-level report (focused on "what happened") and Meaning Construction (focused on "what it means" or "how it fits into a larger context").

If the reviewer discusses the themes, ideas, or meaning of the book and its characters or if they make any internal/external connections to other books or to other things in the world, then code as a 1. 

Otherwise, code as a 0.

If the reviewer just recaps the plot of the book, with no additional interpretation, code as 0.

Return only:
0 or 1

Review:
{text}
""",
    "Thought-Provoking": """
Thought-Provoking captures whether the book acted as a catalyst for the reviewer's internal reflection. It distinguishes between a book that was simply "consumed" (for pleasure or information) and a book that "lingered" in the reviewer’s mind, prompting deeper inquiry or a shift in focus.

If the reviewer indicates that the book made them think, prompted questions, sparked reflection, caused the reviewer to pause and consider something new, or was challenging, then code as a 1. 

Otherwise, code as a 0.

Return only:
0 or 1

Review:
{text}
""",
    "Ease": """
Ease assesses whether the reviewer presents the overall reading experience as smooth, absorbing, manageable, or easy to continue.
Code as 1 when the review, taken as a whole, suggests that reading felt enjoyable, flowing, fast-moving, comfortable, or low in resistance.
Minor moments of confusion, slowness, or frustration do not require a 0 if the overall experience remains clearly absorbing and positive.
Code as 0 when the reading experience is mainly described as confusing, effortful, frustrating, exhausting, slow, or difficult to continue.
General praise alone is not enough. Consider the overall balance of evidence, not isolated positive or negative words.
When unclear, code as 0.

RETURN ONLY:
0 or 1

Review:
{text}
""",
    "Critic": """
Critic measures whether the reviewer gives a reasoned or specific evaluation of how the book works, rather than only giving a reaction, summary, interpretation, or personal impact.
Code as 1 when the reviewer evaluates specific aspects of the book, such as plot, characters, writing, structure, pacing, themes, style, worldbuilding, or author choices, and gives a reason, example, comparison, or specific criticism/praise that goes beyond simply saying the book is good or bad.
The explanation may be brief and informal. Formal literary analysis is not required.
Code as 0 when the review mainly gives a rating, recommendation, plot summary, personal reaction, or unsupported praise/criticism without any specific evaluation of how the book works.
When unclear, code as 0.

Return only:
0 or 1

Review:
{text}
""",
    "Surprise": """
Surprise measures whether the reviewer indicates that the book, or some part of it, differed from their own expectations or genuinely caught them off guard.
Code as 1 when the reviewer clearly signals a mismatch between what they expected and what they experienced, or directly describes something as unexpected or surprising.
Code as 0 when the review only expresses praise, disappointment, preference, comparison, or strong emotion without showing that the reviewer’s prior expectation was contradicted.
Do not infer Surprise from a strong reaction alone.
When unclear, code as 0.

Return only:
0 or 1

Review:
{text}
""",
    "Change": """
Change identifies whether the book caused a fundamental shift in the reader's worldview, beliefs. It looks for evidence of intellectual or personal evolution rather than just a temporary emotional reaction.

If the reviewer indicates that the book caused them to change their mind, update their understanding, challenged their prior assumptions, or otherwise led them to re-evaluate how they think about things in the world, then code as a 1. 

Otherwise, code as a 0.

Return only:
0 or 1

Review:
{text}
"""
}

