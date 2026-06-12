const { submitRatings } = require('./pr_automation_helper');

const ratings = {
  responses: {
    'Response A': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Unsatisfying' // severe usability issue by hardcoding and hallucinating "Lumenad" instead of using placeholders
    },
    'Response B': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying' // beautiful layout, professional transferable skills framing, correct placeholders
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Slightly Satisfying' // good, but assumes hands-on Salesforce experience which wasn't in the original draft, and lacks professional layout details
    }
  },
  comparisons: {
    'B and A': 'Left Much Better',      // Left is B (Highly Satisfying), Right is A (Slightly Unsatisfying) -> Left Much Better
    'C and A': 'Left Better',           // Left is C (Slightly Satisfying), Right is A (Slightly Unsatisfying) -> Left Better
    'C and B': 'Right Better'           // Left is C (Slightly Satisfying), Right is B (Highly Satisfying) -> Right Better
  },
  rationale: `Response B is Highly Satisfying. It provides a beautifully formatted, highly professional cover letter layout (with standard headers and dates) and uses clean placeholders like [Company Name] and [where you found the job listing]. Most importantly, it beautifully translates Rachel's customer experience and project work at ClassPass into highly relevant transferable skills for Salesforce administration (such as system management, technical troubleshooting, and adaptability) without making up non-existent experience.
Response C is Slightly Satisfying. It is a solid rewrite and uses correct placeholders, but it is less complete than Response B and assumes Rachel has direct, hands-on experience with Salesforce (which is not mentioned in her draft), making it slightly less authentic to the user's input.
Response A is Slightly Unsatisfying. Although it attempts a decent rewrite, it suffers from a major usability and hallucination issue: it bizarrely invents and hardcodes the specific company name "Lumenad" multiple times in the cover letter text, even though the user prompt never mentioned this company. This makes the cover letter highly risky and unusable without manual search-and-replace corrections.
Therefore, Response B is the clear winner, Response C is second, and Response A is the worst.`
};

async function main() {
  console.log('Submitting Task 20 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 20 completed and submitted!');
}

main().catch(console.error);
