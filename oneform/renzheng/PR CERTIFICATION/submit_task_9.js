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
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful', // due to "Likely Hip-Hop/Rap" spec error
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Left Much Better',     // Left is B (Highly Satisfying), Right is A (Slightly Satisfying) -> Left Much Better
    'C and A': 'Right Better',          // Left is C (Slightly Satisfying with genre error), Right is A (Slightly Satisfying and accurate) -> Right Better
    'C and B': 'Right Much Better'      // Left is C (Slightly Satisfying), Right is B (Highly Satisfying) -> Right Much Better
  },
  rationale: `Response B is outstanding. It not only correctly classifies the text as song lyrics but also identifies the exact iconic song ("We're Not Gonna Take It" by Twisted Sister). It then provides highly accurate sub-classifications under rock music and protest lyrics.
Response A is correct and truthful, but extremely generic, only classifying it as song lyrics without identifying the classic piece.
Response C provides some structured categorization but introduces a minor speculative error, claiming the genre is "Likely Hip-Hop/Rap," which is stylistically incorrect for this famous 1984 glam metal anthem. It also fails to identify the song.
Therefore, Response B is Highly Satisfying and much better than both A and C, while Response A is Better than C due to its accuracy.`
};

async function main() {
  console.log('Submitting Task 9 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 9 completed and submitted! Moving to Task 10...');
}

main().catch(console.error);
