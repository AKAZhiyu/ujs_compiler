%{
#include <stdio.h>
#include <stdlib.h>
%}

ws          [ \t\n]+
letter      [A-Za-z]
digit       [0-9]
id          {letter}({letter}|{digit})*
num         {digit}+
any         .

%%

{ws}        { /* Ignore white space. */ }
"while"     { printf("(1, %s)\n", yytext); }
"if"        { printf("(2, %s)\n", yytext); }
"else"      { printf("(3, %s)\n", yytext); }
"switch"    { printf("(4, %s)\n", yytext); }
"case"      { printf("(5, %s)\n", yytext); }
{id}        { printf("(6, %s)\n", yytext); }
{num}       { printf("(7, %s)\n", yytext); }
"+"         { printf("(8, %s)\n", yytext); }
"-"         { printf("(9, %s)\n", yytext); }
"*"         { printf("(10, %s)\n", yytext); }
"<="        { printf("(11, %s)\n", "LE"); }
"<"         { printf("(11, %s)\n", "LT"); }
"=="        { printf("(11, %s)\n", "EQ"); }
"="         { printf("(12, %s)\n", yytext); }
";"         { printf("(13, %s)\n", yytext); }
"("         { printf("(14, %s)\n", yytext); }
")"         { printf("(15, %s)\n", yytext); }
"{"         { printf("(16, %s)\n", yytext); }
"}"         { printf("(17, %s)\n", yytext); }
":"         { printf("(18, %s)\n", yytext); }
{any}       { printf("Error: Unknown token %s\n", yytext); }

%%

int yywrap() {
   return 1;
}

int main(int argc, char **argv) {
    if(argc > 1) {
        if(!(yyin = fopen(argv[1], "r"))) {
            perror(argv[1]);
            return 1;
        }
    }

    while(yylex());
    return 0;
}