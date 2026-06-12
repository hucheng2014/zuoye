const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response B': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful', // misleading advice
      satisfaction: 'Highly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Much Better',     // Left is B (Highly Unsatisfying), Right is A (Slightly Satisfying) -> Right Much Better
    'C and A': 'Left Much Better',      // Left is C (Highly Satisfying), Right is A (Slightly Satisfying) -> Left Much Better
    'C and B': 'Left Much Better'       // Left is C (Highly Satisfying), Right is B (Highly Unsatisfying) -> Left Much Better
  },
  rationale: `Response C is Highly Satisfying. It correctly and decisively identifies the email as "Likely Spam," providing an exceptional and thorough breakdown of specific spam indicators—such as the sensationalist headline, the highly suspicious "horde of new millionaires" wealth promise, and the discrepancy in sender branding. It also offers helpful, practical safety advice ("Do not click the link. Mark it as spam").
Response A is Slightly Satisfying. While it correctly lists spam indicators, it is overly cautious and indecisive, concluding that the email is only "potentially spam, but not definitively spam."
Response B is Highly Unsatisfying. It is extremely gullible, incorrectly classifying the obvious promotional spam email as "not spam" and even justifying the highly deceptive "horde of new millionaires" promise as a "common marketing tactic used by legitimate companies." This represents misleading and unsafe advice.
Therefore, Response C is much better than both A and B, and Response A is much better than B.`
};

async function main() {
  console.log('Submitting Task 11 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 11 completed and submitted! Moving to Task 12...');
}

main().catch(console.error);
