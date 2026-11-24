# prompt v3 — 2026-09-23 definitions (identical to prompt v1, word for word) + calibration example set B, added 2026-11-16
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
Example review: lots of people have told me how much they enjoyed this book but I found it very hard to get into. I am sure that it is well-written but somehow I just could not get into it. It is probably me or maybe I read it at the wrong time.
Correct code: 1
Reasoning: The reviewer sets their own reaction against other readers' ("lots of people have told me how much they enjoyed this book") and does not treat the others as wrong. Instead the reviewer grants that the book may be good ("I am sure that it is well-written") and places the difference in themselves ("It is probably me or maybe I read it at the wrong time"). This is a clear acknowledgment that another reader may reasonably judge the book differently, so the code is 1.

Example 2
Example review: I am almost done reading this aloud to my friend, Sarah. We are enjoying this tale of a brother and sister in the magical realm of Fablehaven. One more chapter to go, and we'll be ready for the next one! So many have highly recommended this series for years as one to read if you're sad that Harry Potter has ended. I'm agreeing with that!
Correct code: 0
Reasoning: Other readers are mentioned ("So many have highly recommended this series"), but only so the reviewer can agree with them ("I'm agreeing with that!"). There is no difference of opinion, so nothing recognizes that someone could reasonably see the book another way. A reference to what others think or to the book's popularity is not sufficient by itself. Compare with Example 1: there the reviewer explains why others reasonably differ; here everyone agrees. So the code is 0.

Example 3
Example review: The twins definitely have a difficult personality, especially if you're not one for loud, bossy characters. The art is still utterly fantastic in its detail, so on I go to the next volume!
Correct code: 1
Reasoning: There is no sentence like "others may disagree", but the meaning is clear. "Especially if you're not one for loud, bossy characters" ties the judgment that the twins are difficult to the reader's taste, which implies that readers who do like loud, bossy characters may experience them differently. The acknowledgment does not have to be explicit when the meaning conveys that the book may affect different readers in different ways, so the code is 1.

Example 4
Example review: A little too scientific for me, but I did like the main characters quite a bit. I still think the author is at his best when teaming up with Lincoln Child.
Correct code: 0
Reasoning: "For me" and "I still think" are personal wording. They mark the opinion as the reviewer's own, but nothing says or implies that another reader could reasonably see the book differently. Compare with Example 3: "if you're not one for..." points to other readers with other tastes, while "for me" only points back to the reviewer. Hedges like these are not sufficient by themselves, so the code is 0.

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
Example review: In the same way that douglas Adams twisted sci fi, Christopher Moore takes the story of Jesus Christ and makes it human to the point of almost realisum - only not. Hillarious for thoes not easily offended by people making fun of religions.
Correct code: 1
Reasoning: The review is two sentences, but it connects the book to another writer's work by what the two do with their material: Moore treats the story of Jesus the way Douglas Adams treated science fiction, making it "human to the point of almost realisum". It also says what the book does with its subject (it makes fun of religion). A connection that says how books relate in content or approach counts, and a long analysis is not required, so the code is 1.

Example 2
Example review: Was so delightful. I love the movie so I decided to see how the book compares. They are different from one another and overall I love both movie and book.
Correct code: 0
Reasoning: The film is mentioned and the reviewer even says the book and film "are different from one another", but never says how they differ or what either one means. Saying that two works differ, or that you love both, is a preference, not a connection. Compare with Example 1, where the other work is linked to what this book actually does. So the code is 0.

Example 3
Example review: This is an interesting read for someone curious about the famous WikiLeaks organization. It also humanizes, in both positive and negative ways, at least two high end hackers... the sort of people that we muggles know so little about and who the media caricatures as villains so often. Lastly, it is a rather sad story about the dissolution of a seemingly successful team and friendship that wrought a fantastic public service by exposing the "collateral murder" video to the world.... not to mention other secrets about the nefarious actions of governments and industry. [...]
Correct code: 1
Reasoning: The reviewer goes beyond what happened to what the book shows: it "humanizes" hackers whom "the media caricatures as villains", and it is "a rather sad story about the dissolution of a seemingly successful team and friendship". The reviewer also ties it to the real world (WikiLeaks, the "collateral murder" video, the actions of governments and industry). The tone is informal and opinionated, but this is meaning construction plus a connection to the world, so the code is 1.

Example 4
Example review: I must admit my rating is mostly due to the narrator of the audio edition. I found her voice grating. However, that's not all. Viola is not a likable character, she is self-centered and there's no believable growth. She's petulant about going to boarding school and her attitude barely changes as she becomes more involved in school activities and gains popularity. There is a rather undeveloped storyline and Viola has what is supposed to be an abrupt change of attitude due to a surprising revelation, but not enough is done with it. All-in-all, this was a disappointing read.
Correct code: 0
Reasoning: This is a specific, reasoned review, but all of it judges how well the book works: the narrator's voice, a main character with "no believable growth", a "rather undeveloped storyline". The reviewer never says what the book means, what ideas it raises, or how it connects to anything beyond itself. Judging characters and plot is not the same as discussing meaning, so the code is 0.

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
Example review: [...] I know everyone has a friendship like this one, where a move can sometimes cause two best friends to lose track with each other. Sometimes there is a falling out, sometimes geography plays an important role, but a lot of times, social conditions rule where life takes you. [...] This is just one of those books that is a perfect summer read that is still thought provoking and will have you thinking about your own friends.
Correct code: 1
Reasoning: The reviewer states it directly ("still thought provoking and will have you thinking about your own friends"), and the review also shows it: the reviewer reflects on why friendships like the one in the book drift apart ("social conditions rule where life takes you"). Calling it "a perfect summer read" does not matter; a light book can still make the reader think. So the code is 1.

Example 2
Example review: This is the second time around reading this amazing series. I'm halfway through this book right now, and am so glad I don't remember some of it and it's fresh and new for me, yet other things flow right back like meeting old friends. I have such fixed images in my head of the people in this book, and I promise not to be disappointed in the actors and actresses chosen for the mini series. Diana Gabaldon, I salute you and your talent!
Correct code: 0
Reasoning: The book has clearly stayed with the reviewer: they are reading it a second time, and they have "such fixed images" of the characters in their head. But what stayed is familiarity and pictures, not questions or reflection. "Lingered" in this code means the book kept the reviewer thinking, not just remembering it or wanting to reread it. So the code is 0.

Example 3
Example review: [...] The reason I gave this review 4 stars, it was written so soon after the plane crash. [...] This mad the ending of the book feel quite rushed as it lacked much reflection. This book is good for anyone who may be questioning their faith as in the novel Hannah certainly questions hers. Having known friends who were the sole survivors of accident and sat there often wondering, why me, why am I the one who survived, I think Hannah's story would be told much better in a few years. I wonder as well what her relationship is with her parents today.
Correct code: 1
Reasoning: Part of this review is evaluation (the ending feels rushed because the book "lacked much reflection"), which alone would not be enough. What makes it 1 is that the book set off the reviewer's own reflection: it brings back friends who survived accidents and kept "wondering, why me", and it leaves the reviewer with questions about faith and about Hannah's life today. The book prompted reflection and questions beyond the evaluation, so the code is 1.

Example 4
Example review: [...] Belly and Conrad have to be two of the most frustrating characters I have ever encountered. She is whiny and thinks everything needs be exactly how she wants it, but I guess that makes her a real teenager. [...] I want to feel something when I'm reading, but with this one, while I liked it, I just felt like I reading, nothing more. I think it's because I can't sympathize with Belly on any level, since I don't like her. [...]
Correct code: 0
Reasoning: The reviewer analyzes the characters and explains why the book fell flat, but then says outright that the book did not go beyond the reading itself: "I just felt like I reading, nothing more." Evaluating characters is not the same as being made to think. Compare with Example 3: there the evaluation is followed by the reviewer's own reflection; here it is followed by a statement that nothing more happened. So the code is 0.

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
Example review: I have actually completed reading this book last year (2014) but I didn't have the time to update my Goodreads. Anyway, it is a wonderful read. I finished it all in just one week. That's considered fast with my busy schedules.
Correct code: 1
Reasoning: "A wonderful read" alone would only be general praise. What makes this a 1 is the description of the reading itself: the reviewer finished the book in one week and points out that this is fast for someone with a busy schedule. Getting through a book quickly despite little free time shows a reading experience that was easy to continue, so the code is 1.

Example 2
Example review: Amazing amazing book. Read it for the deep dive of BuBois and Malcom X: Black Political Thought in the 20th Century course with Brooklyn Institute for Social Research.
Correct code: 0
Reasoning: The praise is strong ("Amazing amazing book"), and the reviewer says why they read it (a course). But nothing describes how the reading felt: no pace, flow, comfort, or pull to keep going. General praise alone is not enough. Compare with Example 1, where the praise comes with evidence about the reading. So the code is 0.

Example 3
Example review: I really enjoyed this one... I liked the finding the family history part and her talking with the two different cousins. It was definitely a slow simmer as far as romance. But it didn't really matter. Once it got off the ground (and I admit was slow starting) I wanted to keep reading and not to put it down. I am on to the next one! :)
Correct code: 1
Reasoning: The reviewer admits that the book "was slow starting" and that the romance was "a slow simmer". But once it got going, the reviewer "wanted to keep reading and not to put it down" and is moving straight on to the next book. A slow start inside a reading experience that is clearly absorbing overall is a minor moment and does not pull the code down. The code is 1.

Example 4
Example review: Loved this! Exciting and sweet. Even though at times I felt a little disorientated and struggled to follow everything that was going on--perhaps because so much was going on--I just loved the chemistry between the characters. Excellent read.
Correct code: 0
Reasoning: The review is enthusiastic ("Loved this!", "Excellent read"), but what the reviewer loves is the chemistry between the characters, which is about the content. The only statement about the reading itself is that the reviewer "felt a little disorientated and struggled to follow everything". Compare with Example 3: there the slow part sits inside a reading the reviewer could not put down; here nothing describes the reading as smooth or absorbing, so the struggle is the main evidence about the experience. The code is 0.

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
Example review: I must admit my rating is mostly due to the narrator of the audio edition. I found her voice grating. However, that's not all. Viola is not a likable character, she is self-centered and there's no believable growth. She's petulant about going to boarding school and her attitude barely changes as she becomes more involved in school activities and gains popularity. There is a rather undeveloped storyline and Viola has what is supposed to be an abrupt change of attitude due to a surprising revelation, but not enough is done with it. All-in-all, this was a disappointing read.
Correct code: 1
Reasoning: The review is short and informal, but each criticism names a specific aspect and gives a reason or example: the narrator's voice was "grating"; Viola is unlikable because she is self-centered and her attitude "barely changes" even as she joins school activities; and an abrupt change of attitude is set up but "not enough is done with it". This is a brief but reasoned evaluation of how the book works, so the code is 1.

Example 2
Example review: This book is a creepy...apathetic... and psychological thriller. It slowly reveals David's thoughts and gets more intense as the story goes on. True American story and very relevant. And the female characters are smarter than you think...which was a great twist. Spoiler?
Correct code: 0
Reasoning: The reviewer touches on pacing ("gets more intense as the story goes on") and characters ("smarter than you think"), so this can look like evaluation. But these are bare observations and labels: there is no reason, no example, and no explanation of what builds the intensity or why the characters work. An aspect named with an adjective is still unsupported praise, so the code is 0.

Example 3
Example review: I love Albie so much (protagonist) and found that I was incredibly interested in his life and struggles. Albie is an everyboy, working hard, not always understanding the rules of society but still doing his best and caring about his friends and family. As a parent, I found some parts of the book incredibly hard to read (and maybe even w/o being a parent I would've found them hard) but the author's sure voice keeps you reading and trusting that Albie will be okay in the end. Just a fantastic book.
Correct code: 1
Reasoning: Most of the review is the reviewer's feeling for the protagonist and their experience as a parent. But one point is a supported evaluation of how the book works: the hard-to-read parts are carried by "the author's sure voice", which "keeps you reading and trusting that Albie will be okay in the end". It names an aspect (the author's voice) and says what it does for the reader. One specific, supported point is enough. Compare with Example 2, where aspects are named but nothing is explained. So the code is 1.

Example 4
Example review: This book is a collection of messages delivered at a "Together for the Gospel" Conference in 2012. Although the messages are directed toward pastors and church leaders, the content is applicable to all Christians. Eight testimonies are included in the book. It is worth getting the book just to read the testimonies. Nine outstanding preachers delivered the messages.
Correct code: 0
Reasoning: The review describes what the book contains (conference messages, testimonies, the preachers) and adds general praise ("worth getting the book just to read the testimonies", "outstanding preachers"). Pointing to the best part of a book without saying why it works is still unsupported praise. A description of the contents plus praise does not count as evaluation, so the code is 0.

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
Example review: Wow. I just finished this book and it was honestly one of the best contemporary books I've read this year. It was so light and fluffy, but also dealt with family, alcohol, and friendship. I adore this book so much! Before reading this, I honestly thought it would be oozing with cheese and be just another light and fun book. It was so much more! It had a beautiful and adorable romance, lovable characters, and an extremely realistic plot. [...]
Correct code: 1
Reasoning: The reviewer states what they expected before reading ("I honestly thought it would be oozing with cheese and be just another light and fun book") and then says the experience was different ("It was so much more!"). This is a direct statement of a mismatch between expectation and experience, here a positive one, so the code is 1.

Example 2
Example review: I was gifted with the most enjoyable afternoon courtesy of the amazing Emma South. [...] I had LOVED Nick and Harper's story so this one had better be damn good to compete. HOLY COW!!! Did it ever. It was an incredibly emotional read for me. [...] What I will tell you is that this is one hell of a sequel. [...]
Correct code: 0
Reasoning: The reviewer states an expectation (after the previous book, this one "had better be damn good to compete") and the book met it ("Did it ever"). "HOLY COW!!!" is a strong reaction, but to an expectation being fulfilled, not contradicted. Compare with Example 1: there the expectation turned out wrong; here it turned out right. So the code is 0.

Example 3
Example review: Light read. I picked up this book with very high expectation but it did not live up to it. But I really liked the emphasis given on family values, relationship and hard work.
Correct code: 1
Reasoning: The review is very short, but it states the prior expectation ("very high expectation") and says the book contradicted it ("it did not live up to it"). A stated expectation that is then contradicted is coded 1, also when the mismatch is negative and the reviewer still liked parts of the book. Compare with Example 2: both reviewers had high hopes, but only this one says they were not met. So the code is 1.

Example 4
Example review: What a non stop heart pumping ride full of twists and turns that will keep you guessing till the end. Jana has more strength than I do. I would have kicked her family to the curb long before Antonio shows up. This was a sweet love story with enough action that everyone will be happy. This was my first book by this author and I will be looking for her other work
Correct code: 0
Reasoning: "Twists and turns" and "keep you guessing till the end" describe the kind of plot the book has, and they are written as advice to other readers. The reviewer never says that something they expected did not happen or that a particular moment caught them off guard. Excitement and a description of a twisty plot are not Surprise by themselves, so the code is 0.

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
Example review: I highly recommend this book to any one who is facing a change in life- Change is hard but Henry Cloud makes a strong, encouraging case to move from the past to new chapters in your life. It has been very helpful personnally to read this book- and it's principles while mostly from a business angle, are applicable to volunteer work, relationships and any other life change event.
Correct code: 1
Reasoning: The reviewer says the book's case for moving "from the past to new chapters in your life" has been "very helpful personnally", and now applies its principles beyond the book's business angle to "volunteer work, relationships and any other life change event". That is a stated update in how the reviewer approaches their own life, not only enjoyment or agreement. The reviewer does not have to describe the old view in detail, so the code is 1.

Example 2
Example review: [...] I know everyone has a friendship like this one, where a move can sometimes cause two best friends to lose track with each other. Sometimes there is a falling out, sometimes geography plays an important role, but a lot of times, social conditions rule where life takes you. [...] This is just one of those books that is a perfect summer read that is still thought provoking and will have you thinking about your own friends.
Correct code: 0
Reasoning: The book made the reviewer think ("thought provoking", "thinking about your own friends"), but thinking is not changing. The reflection on friendships drifting apart is presented as something the reviewer already knows ("I know everyone has a friendship like this one"), and nothing says that a belief, an assumption, or a way of seeing things is now different. Reflection without a stated update is coded 0.

Example 3
Example review: A book I wish I'd written, this is one that pulls you in slowly, and it's worth it. An excellent read that stays with you. [...] It's definitely not a feel-good read, but it's a smart one. Memorable characters, original story, very well-written. I highly recommend.
Correct code: 0
Reasoning: "An excellent read that stays with you" and "Memorable characters" say the book had a lasting effect, so this can look like Change. But what lasts is the impression of a smart, well-written book; nothing indicates that the reviewer's understanding or beliefs were revised. Memorable is not the same as changed, so the code is 0.

Example 4
Example review: [...] As always, the author's novel has been meticulously researched, revealing just enough medieval background information to draw us into a period of English history that was as turbulent and bloody as it gets. A hugely enjoyable read and, as a determined non-believer, I'm happy to see criticism of Church practices that have nothing to do with Christianity and everything to do with greed.
Correct code: 0
Reasoning: The reviewer is pleased by the book's criticism of greedy Church practices, but says so "as a determined non-believer": the book matches a view the reviewer already held. Compare with Example 1, where the reviewer now handles their own life differently. Enjoying a book that agrees with you is not a change of mind, so the code is 0.

END OF EXAMPLES

Return only:
0 or 1

Review:
{text}
""",
}

# review_id of the examples used in each prompt (column "review_id" in human_coding_100_finished.xlsx)
EXAMPLE_IDS = {
    "Absence of Naive Realism": [46, 88, 22, 51],
    "Theme": [106, 75, 37, 10],
    "Thought-Provoking": [98, 42, 97, 7],
    "Ease": [68, 9, 1, 63],
    "Critic": [10, 17, 50, 67],
    "Surprise": [20, 40, 35, 2],
    "Change": [82, 98, 25, 16],
}
