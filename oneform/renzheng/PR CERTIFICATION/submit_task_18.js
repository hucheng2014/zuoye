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
      instructionFollowing: 'Partially following', // uses overly casual translation and fails the Odyssey context in the beat
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Unsatisfying' // severe historical/contextual hallucination: Viking longship with bronze roof for Odysseus
    },
    'Response C': {
      instructionFollowing: 'Fully following',
      concision: 'Good',
      truthfulness: 'Truthful',
      satisfaction: 'Highly Satisfying' // perfect contemporary translation and correct structured story beat entry
    }
  },
  comparisons: {
    'C and A': 'Left Better',           // Left is C (Highly Satisfying), Right is A (Slightly Satisfying) -> Left Better
    'C and B': 'Left Much Better',      // Left is C (Highly Satisfying), Right is B (Highly Unsatisfying) -> Left Much Better
    'B and A': 'Right Much Better'      // Left is B (Highly Unsatisfying), Right is A (Slightly Satisfying) -> Right Much Better
  },
  rationale: `Response C is Highly Satisfying. It provides an excellent, natural, contemporary translation of the Odyssey opening that completely avoids slang or Gen Z vernacular. Furthermore, it perfectly follows the instruction to create a "first story beat entry" at the end by formatting it as a proper, structured beat outline entry ("Story Beat Entry: Introduction of Odysseus...").
Response A is Slightly Satisfying. It provides a beautiful contemporary translation. However, its "Story Beat Entry" is written as a fully fleshed-out dramatic narrative prose paragraph rather than a structured story beat entry, which is a minor formatting deviation.
Response B is Highly Unsatisfying. The translation is overly casual and colloquial ("Listen, I want to hear about this guy...", "honestly"), which degrades the tone. More importantly, its story beat entry contains a severe historical and contextual error: it describes Odysseus on a Norse/Viking "longship" with a "bronze roof" during a storm wracked horizon 3 years after the fall of Troy. Odysseus sailed on ancient Greek galleys, and Greek ships did not have bronze roofs. This is a bizarre and historically inaccurate hallucination.
Therefore, Response C is the best, Response A is a solid second, and Response B is the worst.`
};

async function main() {
  console.log('Submitting Task 18 ratings...');
  await submitRatings(ratings);
  console.log('✓ Task 18 completed and submitted!');
}

main().catch(console.error);
