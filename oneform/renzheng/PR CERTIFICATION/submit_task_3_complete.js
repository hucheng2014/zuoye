const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response B': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying'
    }
  },
  comparisons: {
    'A and B': 'Right Better',          // Left is A (Slightly Satisfying), Right is B (Highly Satisfying) -> Right Better
    'A and C': 'Right Better',          // Left is A (Slightly Satisfying), Right is C (Highly Satisfying) -> Right Better
    'B and C': 'Same'                  // B and C are identical -> Same
  },
  rationale: `Response B and Response C are identical and excellent. They provide a direct, concise, and perfectly grammatically correct rewrite that addresses the spelling typo ("athetic" to "athletic") and the phrasing errors cleanly.
Response A followed instructions, but included a factual hallucination in its explanation section, claiming that "athetic" is a real English word referring to "sports performance," which is incorrect (it is simply a spelling typo of "athletic" in this context).
Therefore, Response B and C are Highly Satisfying and identical to each other, while Response A is only Slightly Satisfying due to the factual hallucination in the explanation.`
};

async function main() {
  console.log('Submitting Task 3 complete ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 3 completed and submitted! Moving to Task 4...');
}

main().catch(console.error);
