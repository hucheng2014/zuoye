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
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'A and B': 'Left Better',          // Left is A (Highly Satisfying), Right is B (Slightly Satisfying) -> Left Better
    'A and C': 'Left Better',          // Left is A (Highly Satisfying), Right is C (Slightly Satisfying) -> Left Better
    'B and C': 'Same'                  // B and C are identical -> Same
  },
  rationale: `Response A is excellent. It provides a direct and complete answer ("Titusville, Florida") that accurately captures the location mentioned in the text.
Response B and Response C are identical to each other. They are slightly less complete than Response A as they omit the state "Florida" and describe Titusville as a "town" (it is incorporated as a city).
Therefore, Response A is Highly Satisfying, Response B and C are Slightly Satisfying and identical to each other.`
};

async function main() {
  console.log('Submitting Task 4 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 4 completed and submitted! Moving to Task 5...');
}

main().catch(console.error);
