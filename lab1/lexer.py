import sys

# 关键字、分隔符、运算符常量定义
KEYWORDS = {
    "if", "else", "while", "break", "continue", "for", "double", "int",
    "float", "long", "short", "switch", "case", "return", "void"
}

SEPARATORS = {"{", "}", "[", "]", "(", ")", "~", ",", ";", ".", "?", ":"}

OPERATORS = {
    "+", "++", "-", "--", "+=", "-=", "*", "*=", "%", "%=", "->", "|", "||", 
    "|=", "/", "/=", ">", "<", ">=", "<=", "=", "==", "!=", "!"
}

# 将类别名称与数值ID关联的字典
CATEGORY_IDS = {
    "double": 265, "int": 266, "break": 268, "else": 3, "switch": 4, "case": 5,
    "char": 276, "return": 278, "float": 281, "continue": 284, "for": 285,
    "void": 287, "do": 292, "if": 2, "while": 1, "static": 295, "{": 299, "}": 300,
    "[": 301, "]": 302, "(": 303, ")": 304, "~": 305, ",": 306, ";": 307, "?": 310,
    ":": 311, "<": 314, "<=": 11, ">": 316, ">=": 317, "=": 318, "==": 319, "|": 320,
    "||": 321, "|=": 322, "^": 323, "^=": 324, "&": 325, "&&": 326, "&=": 327,
    "%": 328, "%=": 329, "+": 8, "++": 331, "+=": 332, "-": 9, "--": 334,
    "-=": 335, "->": 336, "/": 337, "/=": 338, "*": 10, "*=": 340, "!": 341,
    "!=": 342, "ID": 256, "INT10": 346, "FLOAT": 347, "STRING": 351
}


# 当前处理的字符索引（在当前行内）
current_row = -1
# 当前处理的行索引
current_line = 0
# 存储文件内容的列表，每个元素是一行文本
input_str = []

def read_source_file(file_path):
    """读取指定路径的源文件内容，每行作为列表的一个元素存入全局变量input_str。"""
    global input_str
    with open(file_path, "r") as file:
        input_str = file.readlines()

def getchar():
    """从input_str中逐字符读取当前字符，并自动更新行和字符的索引。
    
    返回:
        当前字符，如果到达文件末尾，则返回'SCANEOF'。
    """
    global current_row, current_line
    current_row += 1
    # 当前行读取完毕，转到下一行
    if current_row >= len(input_str[current_line]):
        current_line += 1
        current_row = 0
        # 文件读取完毕
        if current_line >= len(input_str):
            return "SCANEOF"
    return input_str[current_line][current_row]

def ungetc():
    """将最近一次由getchar()读取的字符退回，减少行或字符的索引。"""
    global current_row, current_line
    current_row -= 1
    # 如果退回到当前行的开始，则退回到上一行的末尾
    if current_row < 0:
        current_line -= 1
        current_row = len(input_str[current_line]) - 1

def lexical_error(message):
    """打印当前位置的词法错误信息。"""
    print(f"Lexical error at {current_line+1}:{current_row+1}: {message}")

def scanner():
    """扫描器主循环，从文件中逐个读取字符，获取并处理词法单元，直到文件结束。"""
    while True:
        token = get_next_token()
        if token is None:
            continue
        elif token == "SCANEOF":
            break
        else:
            print(token)

def get_next_token():
    """识别并返回下一个词法单元，基于当前读取的字符和预定义的词法规则。
    
    返回:
        词法单元或None，如果是空白字符则忽略。
    """
    current_char = getchar()
    if current_char == "SCANEOF":
        return "SCANEOF"
    elif current_char.isspace():
        return None

    # 根据字符的类型处理对应的词法单元
    if current_char.isdigit():
        return handle_number(current_char)
    elif current_char.isalpha() or current_char == "_":
        return handle_identifier(current_char)
    elif current_char == '"':
        return handle_string()
    elif current_char == '/':
        return handle_comment()
    elif current_char in SEPARATORS:
        return ("SEP", current_char, CATEGORY_IDS[current_char])
    elif current_char in OPERATORS:
        return handle_operator(current_char)
    else:
        lexical_error("Unknown character")

def handle_number(char):
    """从输入中提取整数或浮点数，返回相应的词法单元。"""
    number = char
    while (char := getchar()).isdigit():
        number += char
    if char != ".":
        ungetc()  # 如果字符不是点，退回这个字符
        return ("INT", number, CATEGORY_IDS["INT10"])
    # 处理小数部分
    number += char + get_decimal_part()
    return ("FLOAT", number, CATEGORY_IDS["FLOAT"])

def get_decimal_part():
    """提取数字的小数部分。"""
    decimal = ""
    while (char := getchar()).isdigit():
        decimal += char
    ungetc()  # 退回非数字字符
    return decimal

def handle_identifier(char):
    """识别标识符或关键字，返回相应的词法单元。"""
    identifier = char
    while (char := getchar()).isalnum() or char == "_":
        identifier += char
    ungetc()  # 退回非标识符部分的字符
    # 判断是否为关键字
    if identifier in KEYWORDS:
        return (identifier.upper(), "", CATEGORY_IDS[identifier])
    return ("ID", identifier, CATEGORY_IDS["ID"])

def handle_string():
    """从输入中提取字符串字面量，直到遇到结束引号。"""
    str_literal = ""
    while (char := getchar()) != '"':
        if char == "SCANEOF":
            lexical_error('Missing terminating quote')
            return "SCANEOF"
        str_literal += char
    return ("STRING_LITERAL", str_literal, CATEGORY_IDS["STRING"])

def handle_comment():
    """处理可能的注释，单行或多行。"""
    next_char = getchar()
    if next_char == "*":
        # 处理多行注释
        if skip_multiline_comment():
            return None
        return "SCANEOF"
    ungetc()  # 退回字符，可能不是注释的开始
    return handle_operator('/')

def handle_operator(first_char):
    """识别和处理操作符，可能包含多个字符。"""
    if (second_char := getchar()) in OPERATORS:
        combined = first_char + second_char
        if combined in CATEGORY_IDS:
            return ("OP", combined, CATEGORY_IDS[combined])
    ungetc()  # 退回第二个字符
    return ("OP", first_char, CATEGORY_IDS[first_char])

def skip_multiline_comment():
    """跳过多行注释内容，直到遇到结束符号。"""
    while True:
        char = getchar()
        if char == "*":
            if (next_char := getchar()) == "/":
                return True
            ungetc()  # 退回非结束符号的字符
        elif char == "SCANEOF":
            lexical_error("Unterminated multiline comment")
            return False

def main():
    """程序主入口，处理命令行参数。"""
    if len(sys.argv) > 1:
        read_source_file(sys.argv[1])
        scanner()
    else:
        print("No file provided.")

if __name__ == "__main__":
    main()
