# prompt v4 — 2026-09-23 definitions (identical to prompt v1, word for word) + calibration example set C, added 2026-11-16
# Same definitions as v1/v2, different examples: v2 = set A (groupcoding.xlsx), v3 = set B, v4 = set C.
# Set B and set C come from human_coding_100_finished.xlsx (B120 batch) and share no reviews with each other or with set A.
# EXAMPLE_IDS (bottom of file) lists the review_id of every example per code. When you score a code against the
# human labels, drop those reviews for that code: the prompt already contains their answer.

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

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: [...] Definitely not my favorite books, but I did enjoy Alice's Adventures in Wonderland more than Through the Looking Glass. I'm not going to say don't read this because I know a great deal of people enjoy this classic...it's just that I didn't find it all that great. Nevertheless, if you find the time, pick it up if you want to. It's a quick read and you can make your own judgment about it.
Correct code: 1
Reasoning: The reviewer explicitly sets their own lukewarm view against the many readers who enjoy the book ("I know a great deal of people enjoy this classic...it's just that I didn't find it all that great"), declines to treat their view as the correct one ("I'm not going to say don't read this"), and invites the reader to "make your own judgment". This is a clear acknowledgment that another reader may reasonably judge the book differently, so the code is 1.

Example 2
Example review: I'm torn in two now after reading this book by Natalie. [...] This book runs along with book 1 time line but is from Connor Riley's point of view, I'm so glad we got his story it's a great read and I'm sure your going to love him even if you don't want too! A note though read Broken Ever After first, Then you can torture yourself about falling for the so called bad guy too :). [...]
Correct code: 0
Reasoning: The reviewer talks to other readers, but only to predict that they will react the same way ("I'm sure your going to love him even if you don't want too", "falling for the so called bad guy too"). Being "torn in two" is the reviewer's own mixed feeling, not a recognition that others may see the book differently. Compare with Example 1: there other readers' different view is accepted; here other readers are expected to agree. So the code is 0.

Example 3
Example review: I bought this book on Amazon for the great price of $0.99. I just want to start off by saying that this book is very dark. There may even be things that might offend some people. It really depends on your personal preference. However, I did keep reading no matter what I came up to. [...] If you enjoy reading a book about a different time, and a different world, then this could be the book for you. [...]
Correct code: 1
Reasoning: The reviewer says plainly that reactions to the book's dark content will vary ("There may even be things that might offend some people. It really depends on your personal preference"), presents their own choice to keep reading as just their response ("However, I did keep reading"), and ends by tying the recommendation to the reader's taste ("If you enjoy reading a book about a different time... then this could be the book for you"). This acknowledges that the book may affect different readers in different ways, so the code is 1.

Example 4
Example review: Some brilliant writing here -- captivating. I enjoyed it all but the bridge story seemed to lose its objective when the protagonist got on the train. Best bit for me was the barbarian's trip through the underworld. Some of the parts were great but the total was less than the sum of the parts - I think!
Correct code: 0
Reasoning: "Best bit for me", "seemed" and "I think!" are personal wording and hedges. They mark the opinions as the reviewer's own and a little uncertain, but nothing says or implies that another reader could reasonably see the book differently. Compare with Example 3: there the reviewer points to other readers with other preferences; here the hedges only point back to the reviewer. Hedges are not sufficient by themselves, so the code is 0.

END OF EXAMPLES

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

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: I loved the book. Very realistic and accurate compared to the Bible. It is fiction, but based on historical facts about the region and times. This is book 1 in a new series. I have just ordered the next two books.
Correct code: 1
Reasoning: The review is short and does not discuss themes, but it connects the novel to things outside it: the Bible ("Very realistic and accurate compared to the Bible") and the real history of the place and period ("based on historical facts about the region and times"). Under this code, a connection to other books or to things in the world is enough by itself, so the code is 1.

Example 2
Example review: This is Steven James' best book so far. I feel that he used all his experience in writing his Patrick Bowers series and put it into this one book.
Correct code: 0
Reasoning: Another series by the same author is mentioned, but only to rank this book ("best book so far") and to credit the author's experience. The reviewer says nothing about what either book is about or how they relate in ideas or content. Naming another title to say better or worse is a preference, not a connection. Compare with Example 1, where the outside reference is about the book's content. So the code is 0.

Example 3
Example review: Fat Girl is the incredibly depressing account of an insecure woman's loveless childhood. [...] But it's a nice reminder that fat doesn't happen in a vacuum. Fat is genetics, abuse, diet culture, and the abundance of food that's strategically designed to entice and to sell, sell, sell. Fat will happen in our culture. It just will. It's cruel and pointless to punish fat people, when the problem (if we can call it that) is all of ours.
Correct code: 1
Reasoning: The wording is blunt and opinionated, but the reviewer reads the memoir as saying something about the world: weight "doesn't happen in a vacuum"; it comes from "genetics, abuse, diet culture" and food marketing; and the problem "is all of ours". The reviewer interprets what the book means and connects it to society outside the book. Informal interpretation is still meaning construction, so the code is 1.

Example 4
Example review: [...] I enjoyed this book, especially the first two parts. My only quibble was with the ending, as I would have liked to have seen how Lena turned out and whether anythig blossomed romantically between Rob and Rebecca. I feel like those were loose ends left untied, almost like it needed a sequel. [...] It pretty much kicks off from the get go and I also did like the characters and vivid descriptions of the Isle of Man. [...] Definitely a good read for anyone into espionage/crime novels, and all that kind of thing.
Correct code: 0
Reasoning: The reviewer evaluates the ending (loose ends), the pace, the characters and the descriptions, and says who will like the book. "Vivid descriptions of the Isle of Man" praises how the setting is written, and "espionage/crime novels" names the genre for a recommendation; neither says what the book means or links its ideas to anything. Judging the quality of a book is not the same as discussing its meaning, so the code is 0.

END OF EXAMPLES

Return only:
0 or 1

Review:
{text}
""",
    "Thought-Provoking": """
Thought-Provoking captures whether the book acted as a catalyst for the reviewer's internal reflection. It distinguishes between a book that was simply "consumed" (for pleasure or information) and a book that "lingered" in the reviewer’s mind, prompting deeper inquiry or a shift in focus.

If the reviewer indicates that the book made them think, prompted questions, sparked reflection, caused the reviewer to pause and consider something new, or was challenging, then code as a 1. 

Otherwise, code as a 0.

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: I've always had an innate fascination and interest with Holocaust novels, and movies. [...] I don't believe many people think about how WWII affected the German people, a few years ago I spent quite some time with a patient of mine who was from Germany. She told me a lot about her life and the struggles of her family during the Holocaust. So, to say the least this book really pulled on my heart strings to imagine a child on either side of this war battling things like this while not being able to feel like they can actually 'do' something about it. [...]
Correct code: 1
Reasoning: There is no phrase like "made me think", but the review shows the reflection. The book led the reviewer to consider a side of the war that she believes few people think about, to connect it with what a German patient once told her, and to imagine "a child on either side of this war" unable to do anything about it. Being led to consider something new counts. The emotion ("pulled on my heart strings") alone would not be enough; what counts is the reflection that comes with it. So the code is 1.

Example 2
Example review: I didn't know what to write about this book and I still kind of don't. It was the perfect balance of thriller/suspense and romance. I loved it. It was heartbreaking but hopeful. It was exhilarating and calming. I was enthralled from start to finish.
Correct code: 0
Reasoning: "I didn't know what to write about this book and I still kind of don't" shows how strongly the reviewer felt, and the rest is a list of feelings ("heartbreaking but hopeful", "exhilarating and calming", "enthralled"). But nothing indicates that the book raised a question or made the reviewer reconsider anything. Strong feelings are not reflection. Compare with Example 1: both reviews are emotional, but only there does the emotion come with something the reviewer thinks about. So the code is 0.

Example 3
Example review: [...] It's set in a time when London has a sophisticated web system--a kind of natural extension of the present world wide web--run by the Portal company. [...] Sensors line the street so that people can be located at any time. This alone has made London safer. [...] The benefits seem to outweigh the disadvantages. It's a beneficial big brother--or is it? It's a chilling vision because it's all too possible. [...] The plot and pacing are impeccable, and the characters and their relationships are well developed and realistic. [...]
Correct code: 1
Reasoning: Most of the review describes the setting and judges the plot, which alone would not be enough. But the reviewer turns the setting into a question about the real world ("It's a beneficial big brother--or is it?") and calls it "a chilling vision because it's all too possible". The book prompted the reviewer to question something beyond the story, so the code is 1.

Example 4
Example review: [...] I enjoyed this book, especially the first two parts. My only quibble was with the ending, as I would have liked to have seen how Lena turned out and whether anythig blossomed romantically between Rob and Rebecca. I feel like those were loose ends left untied, almost like it needed a sequel. [...] It pretty much kicks off from the get go and I also did like the characters and vivid descriptions of the Isle of Man. [...] Definitely a good read for anyone into espionage/crime novels, and all that kind of thing.
Correct code: 0
Reasoning: The reviewer judges the ending, the pace and the characters. The wish to see "how Lena turned out" is a complaint about loose ends in the plot, not a question the book made the reviewer think about. Nothing indicates reflection, a question, or a challenge; this is an assessment of an enjoyable read. An evaluation without any sign of reflection is coded 0.

END OF EXAMPLES

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

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: This was a fun quick read perfect for staying up all night taking care of a sick kid. Will I read the sequels? I don't know; I liked the characters a lot but the amount of action was more than I lean towards.
Correct code: 1
Reasoning: "A fun quick read" describes the reading itself, and the reviewer adds that it was "perfect for staying up all night taking care of a sick kid", which points to a book that was easy to keep going with under tiring conditions. The doubt about the sequels is about how much action the reviewer likes, a matter of taste, not of difficulty. So the code is 1.

Example 2
Example review: This is Steven James' best book so far. I feel that he used all his experience in writing his Patrick Bowers series and put it into this one book.
Correct code: 0
Reasoning: The review praises the author ("best book so far", "used all his experience"), but nothing describes how the reading felt: no pace, flow, comfort, or pull to keep going. General praise alone is not enough. Compare with Example 1, where the review describes the reading itself. So the code is 0.

Example 3
Example review: This is a book about rabbits, but is really a parallel to human lives and how we react to circumstances. I really enjoyed this book, it has a completely fresh perspective and held my attention well. I think it could have been 50 pages shorter and kept the pacing more even.
Correct code: 1
Reasoning: "Held my attention well" describes an absorbing reading experience. The wish that it "could have been 50 pages shorter and kept the pacing more even" is a minor complaint that does not turn the overall experience negative; the reviewer "really enjoyed" the book. The code is 1.

Example 4
Example review: I did get through this book a little quicker than I normally do, mostly due to skipping over a chapter or two that didn't relate to me as I don't have kids yet & just couldn't couldn't relate to those two chapters (& only reason why it got a 4 star from me) otherwise, this was a good read & I enjoyed it :)
Correct code: 0
Reasoning: Reading fast can show ease (as in Example 1), but here the reviewer explains the speed: "mostly due to skipping over a chapter or two" that they could not relate to. A book read quickly because parts were skipped is not a smooth or absorbing read, and nothing else describes the reading as easy or enjoyable. So the code is 0.

END OF EXAMPLES

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

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: My 1 star is generously brought to you by the last 10% of the book. I'm not a bra burning women's liberation member but could Lexi be any more pathetic? Jack didn't own a single quality to draw me into Lexi's addiction to him so the whole plot line to me was lacking & empty of meaning. Ramsey was the only redeeming part of this book, even Lexi & Chyna's friendship lacked any believable grounding, basically they were clubbing mates, I felt no real deep rooted friendship. [...]
Correct code: 1
Reasoning: A harsh and informal review, but the criticisms name specific aspects and explain them: the love interest "didn't own a single quality to draw me into Lexi's addiction to him", so the plot felt "lacking & empty of meaning"; the friendship "lacked any believable grounding" because "basically they were clubbing mates". Criticism with reasons attached is evaluation, even when it is blunt, so the code is 1.

Example 2
Example review: This was a page turner. Though the plot line is not very feasible, the hero and heroine captured my heart and I thoroughly enjoyed the book. A very good Scottish medieval romance.
Correct code: 0
Reasoning: "The plot line is not very feasible" names an aspect and judges it, but gives no reason or example of what is not feasible. The rest is personal reaction ("captured my heart", "thoroughly enjoyed") and a genre label. Compare with Example 1, where each judgment comes with a reason. A bare judgment of an aspect is still unsupported criticism, so the code is 0.

Example 3
Example review: This book is why I love historical fiction. It was well written. The characters were well developed and history was brought to life. There was only one slip-up that I could see and that was when one character is beheaded and relates being greeted on the other side. Um....I like the idea that the person was greeted by family there, but really....I don't think there is a way the character could record that for us in the story - just sayin'. [...]
Correct code: 1
Reasoning: The general praise ("well written", "characters were well developed") would not be enough on its own. What makes this a 1 is one specific, reasoned criticism: a beheaded character describes being greeted on the other side, which, the reviewer points out, cannot work within the story because the character could not have recorded it. One concrete, supported point is enough. Compare with Example 2. So the code is 1.

Example 4
Example review: This book contains the 3 novellas that make up the first 3 stories in the Seraph Chronicles. [...] This story sees a return to World War II, this time in North Africa. As in the other stories, this is told through the eyes of someone other than Seraph. Houlihan has written another good story, exploring more aspects of the Cthulhu Mythos, this time ancient serpent races. [...] Overall, this series has been very enjoyable so far, and is a worthwhile addition to the genre.
Correct code: 0
Reasoning: Most of the review describes the book: what it contains, the setting, the narrator, what the story explores. The only evaluative words ("another good story", "very enjoyable", "a worthwhile addition to the genre") are general praise with no reason or example attached. A description plus general praise does not count as evaluation, so the code is 0.

END OF EXAMPLES

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

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: [...] The Peach Keeper did surprise me in one interesting way. In previous books, the magical element has been a dedicated trait of one or more characters. [...] This time, the magic in the story started as a part of the town's past, attributed to a shady character who chose to use his charms against those who trusted him. Later, it seemed to evolve into something that encompassed the town. [...] This all boils down to the fact that I got exactly what I hoped for from a Sarah Addison Allen tale. [...]
Correct code: 1
Reasoning: The reviewer says directly that the book "did surprise me" and explains how: in the author's previous books the magic belonged to individual characters, but here it began as something dark in the town's past. Elsewhere the reviewer says they "got exactly what I hoped for", but Surprise only needs the book, or some part of it, to differ from what the reviewer expected. One clearly described departure from expectations is enough, so the code is 1.

Example 2
Example review: An apparent attempt to mash-up Ready Player One and The Hunger Games, Arena is about as marketable a book concept as one can imagine. [...] The problem is not the author's skills; the problem is that the entire work, from start to finish, is absolutely ENSLAVED by formula and genre tropes. [...] Yes, it's all building up to a massive set-piece battle at the end, and yes, that battle ends exactly as you think it will. There are pleasant moments of writing to be found herein, but there are no surprises of any sort. [...]
Correct code: 0
Reasoning: The reviewer is disappointed, but not because an expectation was contradicted. The complaint is the opposite: the book is formulaic, the final battle "ends exactly as you think it will", and "there are no surprises of any sort". A book that turns out exactly as expected is not Surprise, even when that is a disappointment. So the code is 0.

Example 3
Example review: I have read all of Toni Morrison's books because each seems to impart such in depth understanding of her characters and their motivations, good or bad. Not this one. It starts out strongly, the light-skinned mother giving birth to the blackest skinned baby. [...] The rest of the book seems poorly thought out, a kind of a picaresque novel in which Bride just hits the road, briefly meeting people for better or worse and then moving on. [...] I expect nuanced characters from Morrison and this book is a disappointment.
Correct code: 1
Reasoning: The reviewer spells out the prior expectation (every Morrison book has given "in depth understanding of her characters"; "I expect nuanced characters from Morrison") and then reports that this book broke it ("Not this one", "a disappointment"). Compare with Example 2: both reviewers are disappointed, but only here is the disappointment a stated expectation that was contradicted. A contradicted expectation is coded 1, also when the mismatch is negative.

Example 4
Example review: Giving this a 5 star rating is not much of a surprise since I am a big sucker of hate-love stories. As the saying goes, there is a thin line between love and hate. [...] I love how the author developed Martin's character as the story progresses. He is one of my favorite fiction male character *swoon*. [...]
Correct code: 0
Reasoning: The word "surprise" appears, but it is negated and refers to the rating: given the reviewer's love of hate-love stories, a 5-star rating is predictable. The book delivered the kind of story the reviewer expected to enjoy. Compare with Example 1, where "surprise" refers to something in the book that departed from what the reviewer expected. A surprise word without a mismatch is coded 0.

END OF EXAMPLES

Return only:
0 or 1

Review:
{text}
""",
    "Change": """
Change identifies whether the book caused a fundamental shift in the reader's worldview, beliefs. It looks for evidence of intellectual or personal evolution rather than just a temporary emotional reaction.

If the reviewer indicates that the book caused them to change their mind, update their understanding, challenged their prior assumptions, or otherwise led them to re-evaluate how they think about things in the world, then code as a 1. 

Otherwise, code as a 0.

EXAMPLES
The reviews below were coded by the research team. They show where the line between 0 and 1 falls for this code. Each example gives the review, the correct code, and the reasoning behind it. "[...]" marks text left out of a long review. The examples are for reference only: do not code them and do not mention them in your answer. Apply the same reasoning to the review at the end of this prompt.

Example 1
Example review: [...] I found it horrifying that people would spend all of their lives in a virtual world and yet also identified with it strongly because I am an avid reader who spends most of her time outside of work and family, lost in the world of books. You can see how easy it would be for our world to become that world, some may argue it already is. [...] I'd love to tell you that this inspired me enough to run out directly and start connecting with all my peeps and living my life but truth be told, I'm already lining up my next read...
Correct code: 1
Reasoning: The book led the reviewer to look at her own life differently. She finds a life spent in a virtual world horrifying, then recognizes herself in it as someone who spends most of her free time "lost in the world of books", and concludes that "our world" could easily become that world. This is a re-evaluation of how she sees herself and the world. The last sentence jokes that she has not changed her habits yet, but Change is about how the reviewer thinks, not about acting on it right away, so the code is 1.

Example 2
Example review: I've always had an innate fascination and interest with Holocaust novels, and movies. [...] I don't believe many people think about how WWII affected the German people, a few years ago I spent quite some time with a patient of mine who was from Germany. She told me a lot about her life and the struggles of her family during the Holocaust. So, to say the least this book really pulled on my heart strings to imagine a child on either side of this war battling things like this while not being able to feel like they can actually 'do' something about it. [...]
Correct code: 0
Reasoning: The book made the reviewer reflect and imagine the war from the German side, but reflecting is not changing. The view she expresses is one she held before reading, from a long-standing interest in the period and from a German patient's stories ("I don't believe many people think about how WWII affected the German people"). The book deepened an interest; nothing says it changed her mind or corrected an assumption. Reflection without a stated update is coded 0.

Example 3
Example review: Thoroughly disturbing book on the influence of money on every aspect of our democracy. The extent of the utter disregard for fairness is appalling. Overflowing with examples of greed and misinformation. Heart breaking to anyone who loves America.
Correct code: 0
Reasoning: The reaction is strong ("Thoroughly disturbing", "appalling", "Heart breaking"), and the subject is serious. But a strong reaction to what a book reports is not the same as a change in belief: nothing says the reviewer now understands or sees something differently than before reading. A temporary emotional reaction, however strong, is coded 0.

Example 4
Example review: Fat Girl is the incredibly depressing account of an insecure woman's loveless childhood. [...] But it's a nice reminder that fat doesn't happen in a vacuum. Fat is genetics, abuse, diet culture, and the abundance of food that's strategically designed to entice and to sell, sell, sell. Fat will happen in our culture. It just will. It's cruel and pointless to punish fat people, when the problem (if we can call it that) is all of ours.
Correct code: 0
Reasoning: The reviewer states strong views about weight and society, so this can look like Change. But the book is described as "a nice reminder": it confirms what the reviewer already believes rather than changing it. Compare with Example 1, where the reviewer sees herself differently after reading. Agreement with an existing view is not Change, so the code is 0.

END OF EXAMPLES

Return only:
0 or 1

Review:
{text}
""",
}

# review_id of the examples used in each prompt (column "review_id" in human_coding_100_finished.xlsx)
EXAMPLE_IDS = {
    "Absence of Naive Realism": [58, 69, 43, 81],
    "Theme": [21, 77, 33, 45],
    "Thought-Provoking": [27, 28, 101, 45],
    "Ease": [70, 77, 5, 109],
    "Critic": [104, 26, 72, 65],
    "Surprise": [23, 13, 73, 36],
    "Change": [74, 27, 107, 33],
}
