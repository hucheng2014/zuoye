const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Partially following', // failed negative constraints for 2 items
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    },
    'Response B': {
      instructionFollowing: 'Partially following', // completely failed Indian localization constraint
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Unsatisfying'
    },
    'Response C': {
      instructionFollowing: 'Partially following', // failed negative constraints for 2 items
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Better',          // Left is B (Slightly Unsatisfying), Right is A (Slightly Satisfying) -> Right Better
    'C and A': 'Left Better',           // Left is C (Slightly Satisfying with explanations), Right is A (Slightly Satisfying) -> Left Better
    'C and B': 'Left Better'            // Left is C (Slightly Satisfying), Right is B (Slightly Unsatisfying) -> Left Better
  },
  rationale: `Response C is Slightly Satisfying. It provides highly creative, beautifully tailored names based on sweet Indian foods (like Gulab, Jalebi, Barfi, Saffron, Halwa, Peda) and includes excellent, engaging explanations of the cultural inspiration behind each. However, it failed the negative constraint on two occasions (Kheer Dreams starts with K; Rasgulla Rose starts with R).
Response A is also Slightly Satisfying. It has a great list of Indian sweet-themed names, but it does not provide any explanations and also failed the negative constraint on two occasions (Rasmalai Reverie starts with R; Kaju Kheer Kitchen starts with K). Response C is better than Response A due to the added creativity and helpfulness of its explanations.
Response B is Slightly Unsatisfying. Although it followed the negative constraint perfectly, it completely ignored the major cultural and geographical localization constraint ("I live in India hence the shop name should be suggested accordingly"), providing completely generic Western names (like FlourFusion, CandyCove) that are unhelpful to the user.
Therefore, Response C is the best, followed by Response A, while Response B is the least satisfying.`
};

async function main() {
  console.log('Submitting Task 13 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 13 completed and submitted! Moving to Task 14...');
}

main().catch(console.error);
