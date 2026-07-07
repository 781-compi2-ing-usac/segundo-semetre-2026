grammar MiGramatica;
prog:   stat+ ;

stat:   expr NEWLINE;

expr:   expr ('*'|'/') expr     #MultDiv
    |   expr ('+'|'-') expr     #AddSub
    |   INT                     #Int
    |   '(' expr ')'            #ParenExpr
    ;

NEWLINE : [\r\n]+ ;
INT     : [0-9]+ ;
WS      : [ \t]+ -> skip ;