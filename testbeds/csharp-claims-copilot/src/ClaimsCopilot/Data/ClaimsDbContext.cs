using ClaimsCopilot.Models;
using Microsoft.EntityFrameworkCore;

namespace ClaimsCopilot.Data;

public sealed class ClaimsDbContext(DbContextOptions<ClaimsDbContext> options) : DbContext(options)
{
    public DbSet<LossRunRow> LossRuns => Set<LossRunRow>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<LossRunRow>().HasNoKey().ToView("loss_run_v");
    }
}
