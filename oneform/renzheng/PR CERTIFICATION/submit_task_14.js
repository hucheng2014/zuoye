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
      instructionFollowing: 'Partially following', // failed to include the provided 26 names
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Not following', // failed completely and suffered repetition loop
      concision: 'Bad', // severe repetition loop
      description: 'It could have been made shorter',
      truthfulness: 'Not Truthful',
      satisfaction: 'Highly Unsatisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Much Better',     // Left is B (Highly Unsatisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and A': 'Right Much Better',     // Left is C (Highly Unsatisfying/Broken), Right is A (Highly Satisfying) -> Right Much Better
    'C and B': 'Right Better'           // Left is C (Broken loop), Right is B (Poor but readable) -> Right Better
  },
  rationale: `Response A is Highly Satisfying and absolutely flawless. It followed every single constraint perfectly: it successfully included the 26 provided names in its list, added 74 highly creative and relevant 90s/2000s themed silly names (like Tamagotchi, Furby, Ctrl+Alt+Delete, Beanie Baby), met the exact quantity of 100 names, and kept the tone PG-13.
Response B is Highly Unsatisfying. It completely ignored the core constraint to include the 26 provided names, and its list consists of highly generic names with massive duplicate repetitions (e.g., repeating "Biscuit" and "Marshmallow" up to six times).
Response C is a complete failure and Highly Unsatisfying. It completely ignored the provided names and suffered a catastrophic model collapse/repetition loop, repeating the words "Jurassic Park," "Ghostbusters," and "Seinfeld" hundreds of times.
Therefore, Response A is the clear winner, while Response B is better than the completely broken Response C.`
};

async function main() {
  console.log('Submitting Task 14 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 14 completed and submitted! Moving to Task 15...');
}

main().catch(console.error);
