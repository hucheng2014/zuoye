const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Partially following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response B': {
      instructionFollowing: 'Partially following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following',
      concision: 'Good',
      truthfulness: 'Partially Truthful',
      satisfaction: 'Slightly Unsatisfying'
    }
  },
  comparisons: {
    'A and B': 'Left Slightly Better',     // Left is A (Slightly Satisfying), Right is B (Slightly Satisfying). A has better alphabetization. -> Left Slightly Better
    'A and C': 'Left Better',              // Left is A (Slightly Satisfying), Right is C (Slightly Unsatisfying). A has 7 books vs C's 6 books. -> Left Better
    'B and C': 'Left Better'               // Left is B (Slightly Satisfying), Right is C (Slightly Unsatisfying). B has 7 books vs C's 6 books. -> Left Better
  },
  rationale: `Response A is the best response. It successfully extracts all 7 books mentioned in the text and makes the most successful attempt at alphabetization (sorting the first four books "Billions", "Broca's", "Contact", "Cosmos" perfectly). It fails to use bullets.
Response B also extracts all 7 books, but completely fails to alphabetize them (placing "Billions and Billions" after "Contact"). It also fails to use bullets.
Response C is the weakest as it completely misses the book "Billions and Billions" (mentioned in the text as Sagan's final book), and fails to alphabetize or bullet the list.
Therefore, Response A is slightly better than B, and both are better than Response C.`
};

async function main() {
  console.log('Submitting Task 5 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 5 completed and submitted! Moving to Task 6...');
}

main().catch(console.error);
