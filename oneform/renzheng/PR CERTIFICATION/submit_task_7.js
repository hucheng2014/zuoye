const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful',
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
      truthfulness: 'Partially Truthful',
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Left Better',          // Left is B (Highly Satisfying), Right is A (Slightly Satisfying) -> Left Better
    'C and A': 'Same',                 // Both are Slightly Satisfying with minor truthfulness issues -> Same
    'C and B': 'Right Better'          // Left is C (Slightly Satisfying), Right is B (Highly Satisfying) -> Right Better
  },
  rationale: `Response B is excellent. It correctly identifies all 9 artists on the list who are associated with the 20th century (including René Magritte and Edvard Munch) and correctly excludes the Renaissance master Michelangelo and the 19th-century Romantic painter Eugène Delacroix.
Response A has factual and completeness issues. It completely omitted the artist René Magritte from its analysis. It also incorrectly claimed that most of Henri Matisse's important work was before the 20th century (Fauvism was founded in 1905, and nearly all of Matisse's famous paintings were made in the 20th century).
Response C has a minor factual issue as it grouped Edvard Munch (who lived until 1944 and is a major figure in 20th-century modern expressionism) with Michelangelo and Delacroix as "not 20th-century."
Therefore, Response B is Highly Satisfying and clearly the best, while Responses A and C are both Slightly Satisfying due to minor factual or omission errors.`
};

async function main() {
  console.log('Submitting Task 7 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 7 completed and submitted! Moving to Task 8...');
}

main().catch(console.error);
