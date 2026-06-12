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
    }
  },
  comparisons: {
    'A and B': 'Left Much Better'       // Left is A (Highly Satisfying), Right is B (Slightly Unsatisfying) -> Left Much Better
  },
  rationale: `Response A followed all instructions perfectly. It successfully extracted the articles (with an accurate total count of 22) and a comprehensive list of verbs, and successfully rewrote the text without articles and finite verbs.
Response B successfully removed articles from the rewritten text but completely failed to remove verbs (retaining verbs like "fills", "helps", "mark", "chosen", "cut", "suggesting", "lends", etc.). Its extraction counts (6 articles, 16 verbs) were also highly inaccurate.
Therefore, Response A is Highly Satisfying and Response B is Slightly Unsatisfying, making Response A Left Much Better.`
};

async function main() {
  console.log('Submitting Task 2 ratings (Label-based & Dynamic comparison)...');
  await submitRatings(ratings);
  console.log('✓ Task 2 completed and submitted! Moving to Task 3...');
}

main().catch(console.error);
