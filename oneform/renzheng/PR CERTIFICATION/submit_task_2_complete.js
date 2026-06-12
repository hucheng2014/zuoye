const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying'
    },
    'Response B': {
      instructionFollowing: 'Partially following',
      concision: 'Good',
      truthfulness: 'Partially Truthful',
      satisfaction: 'Slightly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following',
      concision: 'Good',
      truthfulness: 'Not Truthful',
      satisfaction: 'Highly Unsatisfying'
    }
  },
  comparisons: {
    'A and B': 'Left Much Better',     // Left is A (Highly Satisfying), Right is B (Slightly Unsatisfying) -> Left Much Better
    'A and C': 'Left Much Better',     // Left is A (Highly Satisfying), Right is C (Highly Unsatisfying) -> Left Much Better
    'B and C': 'Left Better'           // Left is B (Slightly Unsatisfying), Right is C (Highly Unsatisfying) -> Left Better
  },
  rationale: `Response A followed all instructions perfectly. It successfully extracted the articles (with an accurate total count of 22) and a comprehensive list of verbs, and successfully rewrote the text without articles and finite verbs.
Response B successfully removed articles from the rewritten text but completely failed to remove verbs (retaining verbs like "fills", "helps", "mark", "chosen", "cut", "suggesting", "lends", etc.). Its extraction counts (6 articles, 16 verbs) were also highly inaccurate.
Response C completely failed the rewrite task, keeping almost all articles and verbs in the rewritten text. It also provided a highly incorrect article count (7) and broke character in its intro/outro.
Therefore, Response A is Highly Satisfying, Response B is Slightly Unsatisfying, and Response C is Highly Unsatisfying.`
};

async function main() {
  console.log('Submitting Task 2 complete ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 2 completed and submitted! Moving to Task 3...');
}

main().catch(console.error);
