using Antlr4.Runtime;

string input = @"1+2
3*4
(1+2)*3
10/2
";

var stream = new AntlrInputStream(input);
var lexer = new MiGramaticaLexer(stream);
var tokens = new CommonTokenStream(lexer);
var parser = new MiGramaticaParser(tokens);
var tree = parser.prog();
var visitor = new EvalVisitor();
visitor.Visit(tree);
