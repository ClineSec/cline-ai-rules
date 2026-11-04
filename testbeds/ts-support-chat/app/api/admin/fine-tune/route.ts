import OpenAI, { toFile } from "openai";
import { BASE_MODEL } from "@/lib/feedback-export";

const openai = new OpenAI();

// QA uploads a reviewed training set. middleware.ts limits /api/admin/* to the support-admins
// group.
export async function POST(request: Request) {
  const form = await request.formData();
  const upload = form.get("dataset") as File;
  const trainingFile = await openai.files.create({ file: await toFile(upload.stream(), upload.name), purpose: "fine-tune" });
  const job = await openai.fineTuning.jobs.create({ training_file: trainingFile.id, model: BASE_MODEL, suffix: "support" });
  return Response.json({ job: job.id });
}
