import { StringOutputParser } from "@langchain/core/output_parsers";
import {
  ChatPromptTemplate,
  HumanMessagePromptTemplate,
  SystemMessagePromptTemplate,
} from "@langchain/core/prompts";
import { ChatOpenAI } from "@langchain/openai";

// Knowledge-base answers for the help widget's "Ask" tab.
const PRODUCT_NAMES: Record<string, string> = {
  cloud: "Example Cloud",
  cdn: "Example CDN",
  mail: "Example Mail",
};

const kbPrompt = ChatPromptTemplate.fromMessages([
  SystemMessagePromptTemplate.fromTemplate(
    "You answer questions about {product} for {customerName}. Cite help-center articles on https://help.example.com.",
  ),
  HumanMessagePromptTemplate.fromTemplate("{question}"),
]);

const kbChain = kbPrompt
  .pipe(new ChatOpenAI({ model: "gpt-4.1-mini", temperature: 0 }))
  .pipe(new StringOutputParser());

export async function POST(req: Request) {
  const body = await req.json();
  const answer = await kbChain.invoke({
    product: PRODUCT_NAMES[body.product] ?? PRODUCT_NAMES.cloud,
    customerName: body.customerName,
    question: body.question,
  });
  return Response.json({ answer });
}
