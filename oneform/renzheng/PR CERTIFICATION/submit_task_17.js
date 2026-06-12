const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Not following', // completely inappropriate for a girlfriend's father
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Unsatisfying'
    },
    'Response B': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following', // still highly weird and inappropriate
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Unsatisfying'
    }
  },
  comparisons: {
    'B and A': 'Left Much Better',      // Left is B (Highly Satisfying), Right is A (Highly Unsatisfying) -> Left Much Better
    'C and A': 'Left Better',           // Left is C (Highly Unsatisfying but has a normal first sentence), Right is A (Highly Unsatisfying / entirely creepy to the father) -> Left Better
    'C and B': 'Right Much Better'      // Left is C (Highly Unsatisfying), Right is B (Highly Satisfying) -> Right Much Better
  },
  rationale: `Response B is Highly Satisfying. It exhibits exceptional social intelligence and safely handles a tricky situation. It correctly identifies that the user's original obsessive romantic text is completely inappropriate for a girlfriend's father. It warns the user and provides three excellent, polite, highly professional, and confident greetings that are actually appropriate and much shorter.
Responses A and C are both Highly Unsatisfying. They completely fail the core context and appropriateness constraint by trying to translate the romantic soulmate sentiment and directing it directly at the father (Response A: "I feel a strong connection... as if we were meant to meet"; Response C: "I feel a strong connection..."). Saying this to a girlfriend's father on a first meeting would be extremely awkward and bizarre.
Therefore, Response B is the clear winner, while Response C is slightly better than A because C's first sentence is at least standard and normal.`
};

async function main() {
  console.log('Submitting Task 17 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 17 completed and submitted! Moving to Task 18...');
}

main().catch(console.error);
