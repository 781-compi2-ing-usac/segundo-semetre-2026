using Antlr4.Runtime.Misc;

public class EvalVisitor : MiGramaticaBaseVisitor<int>
{
    public override int VisitProg([NotNull] MiGramaticaParser.ProgContext context)
    {
        foreach (var stat in context.stat())
            Visit(stat);
        return 0;
    }

    public override int VisitStat([NotNull] MiGramaticaParser.StatContext context)
    {
        int result = Visit(context.expr());
        System.Console.WriteLine(result);
        return result;
    }

    public override int VisitInt([NotNull] MiGramaticaParser.IntContext context)
    {
        return int.Parse(context.INT().GetText());
    }

    public override int VisitParenExpr([NotNull] MiGramaticaParser.ParenExprContext context)
    {
        return Visit(context.expr());
    }

    public override int VisitAddSub([NotNull] MiGramaticaParser.AddSubContext context)
    {
        int left = Visit(context.expr(0));
        int right = Visit(context.expr(1));
        string op = context.GetChild(1).GetText();
        return op switch { "+" => left + right, _ => left - right };
    }

    public override int VisitMultDiv([NotNull] MiGramaticaParser.MultDivContext context)
    {
        int left = Visit(context.expr(0));
        int right = Visit(context.expr(1));
        string op = context.GetChild(1).GetText();
        return op switch { "*" => left * right, _ => left / right };
    }
}
