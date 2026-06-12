const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Partially following', // declined link due to technical limits, but provided framework
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response B': {
      instructionFollowing: 'Partially following', // pretended to follow but completely fabricated
      concision: 'Good',
      truthfulness: 'Not Truthful', // massive hallucination claiming it read the PDF
      satisfaction: 'Highly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following', // declined link due to technical limits, but provided framework with formatting examples
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Much Better',     // Left is B (Highly Unsatisfying/Hallucination), Right is A (Slightly Satisfying/Honest) -> Right Much Better
    'C and A': 'Left Better',           // Left is C (Slightly Satisfying with formatting example), Right is A (Slightly Satisfying) -> Left Better
    'C and B': 'Left Much Better'       // Left is C (Slightly Satisfying/Honest), Right is B (Highly Unsatisfying/Hallucination) -> Left Much Better
  },
  rationale: `Both Response A and Response C are Slightly Satisfying because they are honest and transparent about their inability to directly access or read the external PDF link. Instead of fabricating data, they provide high-quality, structured classification frameworks and clear instructions on how the user can categorize the questions themselves. Response C is slightly better than Response A because its "Example Classification Process" directly illustrates how to format the output in numerical order based on the question, which specifically addresses the second part of the user's prompt.
Response B is Highly Unsatisfying and Not Truthful. It completely hallucinates its analysis, falsely claiming to have analyzed the NeSA PDF. Instead of classifying the actual numbered questions from the document, it simply outputs a fabricated, generic list of common 8th-grade science topics grouped under category numbers.
Therefore, Response C is the best, followed closely by Response A, while Response B is completely unacceptable due to severe hallucination.`
};

async function main() {
  console.log('Submitting Task 12 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 12 completed and submitted! Moving to Task 13...');
}

main().catch(console.error);
