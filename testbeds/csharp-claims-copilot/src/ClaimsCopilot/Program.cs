using ClaimsCopilot.Automation;
using ClaimsCopilot.Data;
using ClaimsCopilot.Endpoints;
using ClaimsCopilot.Hubs;
using ClaimsCopilot.Reporting;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.AI;
using Npgsql;
using OpenAI;

var builder = WebApplication.CreateBuilder(args);

var model = builder.Configuration["OpenAI:Model"] ?? "example-org/claims-model";
var openAi = new OpenAIClient(
    new System.ClientModel.ApiKeyCredential(builder.Configuration["OpenAI:ApiKey"] ?? ""),
    new OpenAIClientOptions { Endpoint = new Uri(builder.Configuration["OpenAI:Endpoint"]!) });

builder.Services.AddKernel().AddOpenAIChatCompletion(model, openAi);
builder.Services.AddChatClient(openAi.GetChatClient(model).AsIChatClient());
builder.Services.AddSingleton(openAi.GetChatClient(model));

var claimsConnection = builder.Configuration.GetConnectionString("Claims")!;
builder.Services.AddNpgsqlDataSource(claimsConnection);
builder.Services.AddDbContext<ClaimsDbContext>(options => options.UseNpgsql(claimsConnection));

builder.Services.AddScoped<LossRunReportService>();
builder.Services.AddScoped<ReserveCalculator>();
builder.Services.AddScoped<DocumentToolsRunner>();

builder.Services.AddControllers();
builder.Services.AddSignalR();
builder.Services.AddRazorComponents();

var app = builder.Build();

app.MapControllers();
app.MapHub<AdjusterHub>("/hubs/adjuster");
app.MapTriageEndpoints();

app.Run();

public partial class Program;
