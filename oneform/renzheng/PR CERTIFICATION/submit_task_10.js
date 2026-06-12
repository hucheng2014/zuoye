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
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Unsatisfying'
    }
  },
  comparisons: {
    'B and A': 'Same',                  // Both are Highly Satisfying and identical in quality -> Same
    'C and A': 'Right Much Better',     // Left is C (Slightly Unsatisfying), Right is A (Highly Satisfying) -> Right Much Better
    'C and B': 'Right Much Better'      // Left is C (Slightly Unsatisfying), Right is B (Highly Satisfying) -> Right Much Better
  },
  rationale: `Both Response A and Response B are Highly Satisfying. They successfully summarize the text in exactly three concise bullet points and correctly identify that the text is going to give six tips (corresponding to the "6 Fast Facts" / "six ways to get rid of these pesky pests" mentioned multiple times in the article's header and body).
Response C, however, is Slightly Unsatisfying. While its summary is good, it fails to correctly and helpfully answer the second question, claiming it is "impossible to determine" the number of tips. This demonstrates a pedantic misreading of the text and ignores the prominent, explicit title ("6 Fast Facts") and stated intent ("VERIFY six ways").
Therefore, Responses A and B are identical in high quality, and both are much better than Response C.`
};

async function main() {
  console.log('Submitting Task 10 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 10 completed and submitted! Moving to Task 11...');
}

main().catch(console.error);
