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
      satisfaction: 'Highly Satisfying'
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Partially Truthful', // minor inaccuracies about accessing it
      satisfaction: 'Slightly Satisfying'
    }
  },
  comparisons: {
    'B and A': 'Right Better',          // Left is B (Highly Satisfying), Right is A (Highly Satisfying / more precise link explanation) -> Right Better
    'C and A': 'Right Much Better',     // Left is C (Slightly Satisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and B': 'Right Much Better'      // Left is C (Slightly Satisfying), Right is B (Highly Satisfying) -> Right Much Better
  },
  rationale: `Both Response A and Response B are Highly Satisfying. They explain the mechanism beautifully and conversantly to someone who has never used a Google product, using simple and friendly analogies. Response B uses a wonderful "online filing cabinet" analogy, while Response A is slightly better because it is more precise about the actual user experience (explaining that Gmail puts it in Google Drive and creates a link button, rather than saying it is "sent along with the email" as Response B does).
Response C is only Slightly Satisfying. It over-complicates the explanation with a rigid, dense structure and multiple headings, which feels overly technical for a beginner who has "never used a Google product." It also introduces minor inaccuracies, calling Google Drive a "cloud mailbox" and confusingly stating the attachment is "located in Google Drive but you click on it just like a regular email."
Therefore, Response A is the best, followed by Response B, while Response C is much less satisfying.`
};

async function main() {
  console.log('Submitting Task 16 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 16 completed and submitted! Moving to Task 17...');
}

main().catch(console.error);
