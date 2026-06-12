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
      concision: 'Acceptable', // provided multiple options and filler
      description: 'It could have been made shorter',
      truthfulness: 'Partially Truthful', // added subjective unverified adjectives
      satisfaction: 'Slightly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful', // minor factual misinterpretation and subjective adjective
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Much Better',     // Left is B (Slightly Satisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and A': 'Right Much Better',     // Left is C (Slightly Satisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and B': 'Left Better'            // Left is C (Slightly Satisfying / direct single rewrite), Right is B (Slightly Satisfying / indirect options) -> Left Better
  },
  rationale: `Response A is Highly Satisfying. It provides a direct, highly polished, and completely accurate single rewrite that maintains all facts perfectly without introducing any subjective or speculative embellishments.
Response B is Slightly Satisfying. Rather than being direct, it lists three different options accompanied by conversational filler. It also introduces several subjective marketing adjectives (like "stunning," "captivating," "impressive," and "scenic") that are not supported by the objective facts in the source text.
Response C is also Slightly Satisfying. It is a direct and well-written single rewrite, but it introduces a minor factual misinterpretation, claiming the village is "situated southeast of Segou" instead of "in southeast Senegal" (the source states the village is near Segou, in the southeastern region of Senegal). It also adds the speculative adjective "scenic."
Therefore, Response A is the clear winner, and Response C is slightly better than B because it provides a direct, single, polished rewrite instead of listing three options with fluff.`
};

async function main() {
  console.log('Submitting Task 15 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 15 completed and submitted! Moving to Task 16...');
}

main().catch(console.error);
