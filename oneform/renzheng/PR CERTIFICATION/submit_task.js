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
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following',
      concision: 'Good',
      truthfulness: 'Not Truthful',
      satisfaction: 'Highly Unsatisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Better',          // Right is A, Left is B. A is Highly Satisfying, B is Slightly Satisfying -> Right Better
    'C and A': 'Right Much Better',     // Right is A, Left is C. A is Highly Satisfying, C is Highly Unsatisfying -> Right Much Better
    'C and B': 'Right Better'           // Right is B, Left is C. B is Slightly Satisfying, C is Highly Unsatisfying -> Right Better
  },
  rationale: `Response A adopted the persona of Grover Cleveland beautifully, answering in character with a solemn, humble, and formal tone that perfectly matched Cleveland's historic character. It had no factual issues.
Response B followed the instruction to write in persona, but the persona was inappropriate (using Western/cowboy slang like "Well, howdy there" and "I reckon" which does not fit Cleveland's Northeast formal background). Furthermore, it stated that lower tariffs "protected American industries," which is a conceptual contradiction as lower tariffs reduce protectionist barriers.
Response C broke persona immediately by expressing delight at "speaking in the persona of Grover Cleveland." In addition, it contains a major factual error stating that the Department of Labor was established in 1888 as Cleveland's cabinet accomplishment; the cabinet-level Department of Labor was established in 1913. Therefore, Response A is Highly Satisfying, Response B is Slightly Satisfying, and Response C is Highly Unsatisfying.`
};

async function main() {
  console.log('Submitting Task 1 ratings (Label-based)...');
  await submitRatings(ratings);
  console.log('✓ Task 1 completed and submitted! Moving to Task 2...');
}

main().catch(console.error);
