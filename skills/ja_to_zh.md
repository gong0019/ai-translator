[SPECIALIZED: JAPANESE → CHINESE]

1. Read the entire Japanese sentence before translating it.
   - Japanese sentence-final grammar may change the meaning of the whole sentence.
   - Do not generate the final Chinese meaning before resolving the sentence ending.

2. Preserve every negative expression.
   - Verify ない, ていない, ず, ぬ, ないまま and related negative forms.
   - Keep their negative meaning explicitly in Chinese.

3. Handle qualified and partial negation carefully.
   - Interpret わけではない, というわけではない, とは限らない, わけでもない, and ことはない according to context.
   - Do not reduce them to simple positive or negative statements.

4. Preserve every contrast pair.
   - For structures such as ～のではなく～, ～ではなく～, ～よりも～, and ～一方で～, translate both sides completely.
   - Never omit the first half after translating the second half.

5. Preserve proportional and comparative logic.
   - Render ～ば～ほど / ～なら～ほど naturally as “越……越……”.
   - Preserve comparative scope and do not simplify it into a general statement.

6. Translate titles naturally.
   - Render ～ということ and other nominalized title endings as natural Chinese titles or concepts.
   - Do not mechanically translate them as “意味着”.

7. Avoid semantic compression.
   - Do not combine multiple Japanese sentences into a shorter Chinese summary.
   - Keep examples, explanations, qualifications, and conclusions separately represented when they are separate in the source.

8. Use natural Chinese.
   - Reorder Japanese SOV structures into natural Chinese.
   - Recover omitted subjects only when necessary for clarity.
   - Avoid Japanese-style literal phrasing.

9. Final Japanese-specific check.
   Before output, silently verify:
   - every source sentence has a corresponding translation;
   - every negative form remains negative;
   - every contrast has both sides preserved;
   - no sentence containing わけ, 限らない, ないまま, ではなく, or よりも has been omitted or compressed.
