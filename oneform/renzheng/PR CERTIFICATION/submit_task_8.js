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
      truthfulness: 'Not Truthful',
      satisfaction: 'Highly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following', // missed the second bottom layer instruction
      concision: 'Good',
      truthfulness: 'Partially Truthful',
      satisfaction: 'Slightly Unsatisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Much Better',     // Left is B (Highly Unsatisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and A': 'Right Much Better',     // Left is C (Slightly Unsatisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and B': 'Left Better'            // Left is C (Slightly Unsatisfying), Right is B (Highly Unsatisfying) -> Left Better
  },
  rationale: `Response A is mathematically perfect. It correctly calculates that removing the entire outer layer of a 4x4x4 cube reduces the dimensions to a 2x2x2 core, leaving 8 boxes. It then correctly identifies that removing the 2nd layer from the bottom (which is the bottom layer of the 2x2x2 inner core) removes 4 boxes, leaving 4 boxes in total.
Response B is completely incorrect, demonstrating severe math and logical errors (claiming that removing the outer layer only takes away 4 boxes and arriving at an incorrect total of 32).
Response C correctly calculates the first step (8 boxes) but completely ignores the second constraint of the prompt ("plus a 2nd layer on the bottom to make room for foam padding").
Therefore, Response A is Highly Satisfying, Response C is Slightly Unsatisfying, and Response B is Highly Unsatisfying.`
};

async function main() {
  console.log('Submitting Task 8 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 8 completed and submitted! Moving to Task 9...');
}

main().catch(console.error);
