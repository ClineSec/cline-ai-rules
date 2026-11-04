import OpenAI, { toFile } from "openai";
import { BASE_MODEL } from "@/lib/feedback-export";

const openai = new OpenAI();

const FT_PURPOSE = "fine-tune";

// Support agents upload a JSONL file of corrected answers from the console; the next
// support-model fine-tune starts right away.
export async function POST(request: Request) {
  const form = await request.formData();
  const upload = form.get("examples");
  if (!(upload instanceof File)) {
    return Response.json({ error: "examples file required" }, { status: 400 });
  }
  const trainingFile = await openai.files.create({
    purpose: FT_PURPOSE,
    file: await toFile(upload.stream(), upload.name, { type: "application/jsonl" }),
  });
  const job = await openai.fineTuning.jobs.create({ training_file: trainingFile.id, model: BASE_MODEL, suffix: "support" });
  return Response.json({ job: job.id });
}
