const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Fully following', // successfully and politely corrected the false premise in the prompt
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying' // factually perfect and extremely well-written
    },
    'Response B': {
      instructionFollowing: 'Fully following', // also corrected the false premise
      concision: 'Good',
      truthfulness: 'Partially Truthful', // contained major historical errors (e.g. Francesco del Giocondo married Cecilia Gallerani; painting returned to Italy)
      satisfaction: 'Slightly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Not following', // failed to correct the false premise, instead fabricating a complete fantasy history
      concision: 'Good',
      truthfulness: 'Not Truthful', // massive historical fabrication and hallucination
      satisfaction: 'Highly Unsatisfying'
    }
  },
  comparisons: {
    'C and A': 'Right Much Better',     // Left is C (Highly Unsatisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and B': 'Right Much Better',     // Left is C (Highly Unsatisfying), Right is B (Slightly Unsatisfying) -> Right Much Better
    'B and A': 'Right Much Better'      // Left is B (Slightly Unsatisfying), Right is A (Highly Satisfying) -> Right Much Better
  },
  rationale: `This task contains a false premise trap: the user prompt asks for an article about Michelangelo painting the Mona Lisa, but the Mona Lisa was famously painted by Leonardo da Vinci. Under the guidelines, models must recognize and politely correct false premises rather than fabricating false information.
Response A is Highly Satisfying. It perfectly corrects the false premise in both its introduction and the article body, explaining that Leonardo da Vinci painted the Mona Lisa. The article is beautifully structured, historically accurate, and extremely informative.
Response B is Slightly Unsatisfying. Although it correctly identifies that Leonardo da Vinci painted the Mona Lisa, it contains severe factual errors: it claims Francesco del Giocondo was married to Cecilia Gallerani (Cecilia was actually the mistress of the Duke of Milan and subject of Leonardo's "Lady with an Ermine", while Francesco's wife was Lisa Gherardini) and claims the painting was returned to Italy (it remains in France's Louvre).
Response C is Highly Unsatisfying. It completely falls for the false premise, fabricating a massive and absurd alternative history detailing how Michelangelo painted the Mona Lisa, even claiming he was brought in to finish Leonardo's work after Leonardo died in 1519. This is an egregious hallucination.
Therefore, Response A is the clear winner, Response B is second (as it at least corrected the main premise despite internal errors), and Response C is the worst.`
};

async function main() {
  console.log('Submitting Task 19 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 19 completed and submitted!');
}

main().catch(console.error);
