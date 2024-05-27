from pprint import *  # 引入pprint库，用于美化打印输出
import pandas as pd  # 引入pandas库，用于数据处理（虽然此代码片段未使用）
from IPython.display import display, HTML  # 用于在IPython环境中更好地显示结果

class Grammar:
    def __init__(self, grammar_str):
        # 初始化Grammar类
        self.grammar_str = grammar_str  # 存储原始的文法字符串
        self.grammar = {}  # 存储文法的产生式规则
        self.start = None  # 文法的起始符号
        self.terminals = set()  # 终结符集合
        self.nonterminals = set()  # 非终结符集合

        # 解析文法字符串，构建文法的数据结构
        for production in list(filter(None, grammar_str.splitlines())):
            head, _, bodies = production.partition(" -> ")  # 分割产生式的头部和体部

            # 检查产生式的头部是否为大写，确保其为非终结符
            if not head.isupper():
                raise ValueError(f"'{head} -> {bodies}': Head '{head}' is not capitalized to be treated as a nonterminal.")

            # 设置文法的起始符号
            if not self.start:
                self.start = head

            self.grammar.setdefault(head, set())  # 为每个非终结符初始化产生式集合
            self.nonterminals.add(head)  # 添加到非终结符集合
            bodies = {tuple(body.split()) for body in " ".join(bodies.split()).split("|")}  # 处理产生式体部，支持多个产生式选项

            # 遍历每个产生式体部
            for body in bodies:
                if "^" in body and body != ("^",):  # 检查空符号'^'的使用是否合适
                    raise ValueError(f'\'{head} -> {" ".join(body)}\': Null symbol \'^\' is not allowed here.')

                self.grammar[head].add(body)  # 添加产生式到文法结构中

                # 遍历产生式中的每个符号，分类终结符和非终结符
                for symbol in body:
                    if not symbol.isupper() and symbol != "^":
                        self.terminals.add(symbol)  # 添加到终结符集合
                    elif symbol.isupper():
                        self.nonterminals.add(symbol)  # 添加到非终结符集合

        self.symbols = self.terminals | self.nonterminals  # 所有符号集合

def first_follow(G):
    # 定义一个辅助函数union，用于合并集合并检查是否有更新
    def union(set_1, set_2):
        set_1_len = len(set_1)
        set_1 |= set_2  # 合并集合
        return set_1_len != len(set_1)  # 返回是否有元素被添加到集合中

    # 初始化FIRST集和FOLLOW集
    first = {symbol: set() for symbol in G.symbols}
    first.update((terminal, {terminal}) for terminal in G.terminals)  # 终结符的FIRST集是其自身
    follow = {symbol: set() for symbol in G.nonterminals}
    follow[G.start].add("$")  # 起始符号的FOLLOW集中添加'$'

    # 主循环，反复更新FIRST集和FOLLOW集
    while True:
        updated = False  # 用于跟踪是否有更新

        # 遍历文法的每一个产生式
        for head, bodies in G.grammar.items():
            for body in bodies:
                # 遍历产生式体中的每个符号
                for symbol in body:
                    if symbol != "^":  # 如果符号不是空串符号"^"
                        # 将除了空串外的symbol的FIRST集合并到head的FIRST集中
                        updated |= union(first[head], first[symbol] - set("^"))

                        # 如果symbol的FIRST集中没有空串，则中断当前产生式的处理
                        if "^" not in first[symbol]:
                            break
                    else:
                        # 如果是空串符号，直接将空串添加到head的FIRST集
                        updated |= union(first[head], set("^"))
                else:
                    # 如果遍历完整个产生式体没有中断，说明产生式体可完全推导出空串
                    updated |= union(first[head], set("^"))

                # 处理FOLLOW集
                aux = follow[head]  # 开始时，aux设为head的FOLLOW集
                for symbol in reversed(body):
                    if symbol == "^":
                        continue
                    # 将aux中的元素（除空串外）添加到symbol的FOLLOW集中
                    if symbol in follow:
                        updated |= union(follow[symbol], aux - set("^"))
                    # 如果symbol的FIRST集包含空串，则将FIRST集（除空串）合并到aux
                    if "^" in first[symbol]:
                        aux = aux | first[symbol]
                    else:
                        aux = first[symbol]

        # 如果在整个循环中没有发生任何更新，则说明FIRST集和FOLLOW集已稳定，可以终止循环
        if not updated:
            return first, follow



class SLRParser:
    def __init__(self, G):
        # 对输入的文法G进行扩展，添加一个新的起始符号以消除可能的初始冲突
        self.G_prime = Grammar(f"{G.start}' -> {G.start}\n{G.grammar_str}")
        # 计算扩展文法中最长产生式的长度
        self.max_G_prime_len = len(max(self.G_prime.grammar, key=len))
        # 创建一个列表来索引文法的每个产生式，便于后续构建解析表时引用
        self.G_indexed = []

        # 遍历扩展后的文法的每个产生式，并将其添加到索引列表中
        for head, bodies in self.G_prime.grammar.items():
            for body in bodies:
                self.G_indexed.append([head, body])

        # 计算文法的FIRST集和FOLLOW集
        self.first, self.follow = first_follow(self.G_prime)
        # 构建项集族，这是构建SLR解析表的基础
        self.C = self.items(self.G_prime)  # canonical collection
        # 定义解析表中的ACTION部分所需的符号，包括所有终结符和一个特殊的结束符"$"
        self.action = list(self.G_prime.terminals) + ["$"]
        # 定义解析表中的GOTO部分所需的符号，即所有非终结符（不包括新添加的起始符）
        self.goto = list(self.G_prime.nonterminals - {self.G_prime.start})
        # 解析表中所有符号的列表（ACTION和GOTO的合集）
        self.parse_table_symbols = self.action + self.goto
        # 构建SLR解析表
        self.parse_table = self.construct_table()


    def CLOSURE(self, I):
        J = I  # 初始化闭包J为传入的项集I

        # 无限循环直到没有新项可以加入到J中
        while True:
            item_len = len(J)  # 记录当前闭包的大小

            # 遍历J中的每个产生式
            for head, bodies in J.copy().items():
                for body in bodies.copy():
                    # 查找产生式中点符号"."前面的非终结符
                    if "." in body[:-1]:  # 确保点不在产生式的末尾
                        symbol_after_dot = body[body.index(".") + 1]  # 获取点后的符号

                        # 如果点后的符号是非终结符，对应产生式加入到闭包中
                        if symbol_after_dot in self.G_prime.nonterminals:
                            # 获取非终结符的产生式体
                            for G_body in self.G_prime.grammar[symbol_after_dot]:
                                # 向J中添加新的项，项的开始位置是点符号
                                J.setdefault(symbol_after_dot, set()).add(
                                    (".",) if G_body == ("^",) else (".",) + G_body
                                )

            # 如果J的大小未变，结束循环
            if item_len == len(J):
                return J


    def GOTO(self, I, X):
        goto = {}  # 初始化转移后的新状态

        # 遍历项集I中的每个项
        for head, bodies in I.items():
            for body in bodies:
                # 查找点符号"."的位置
                if "." in body[:-1]:  # 确保点不在产生式的末尾
                    dot_pos = body.index(".")
                    
                    # 检查点后的符号是否为X
                    if body[dot_pos + 1] == X:
                        # 构造新的项，将点符号移过符号X
                        replaced_dot_body = (
                            body[:dot_pos] + (X, ".") + body[dot_pos + 2 :]
                        )
                        
                        # 计算新项的闭包，并将结果添加到goto状态
                        for C_head, C_bodies in self.CLOSURE(
                            {head: {replaced_dot_body}}
                        ).items():
                            goto.setdefault(C_head, set()).update(C_bodies)

        return goto

    def items(self, G_prime):
        # 初始项集族C，只包含对文法开始符号的闭包
        C = [self.CLOSURE({G_prime.start: {(".", G_prime.start[:-1])}})]
        
        # 无限循环，直到没有新的项集可以被添加到C中
        while True:
            item_len = len(C)  # 记录当前项集族的长度

            # 遍历当前项集族中的每个项集I
            for I in C.copy():
                # 遍历文法中的所有符号X
                for X in G_prime.symbols:
                    # 使用GOTO函数尝试从项集I通过符号X进行状态转移
                    goto = self.GOTO(I, X)

                    # 如果转移后的项集goto是非空的，并且尚未包含在C中，则添加它
                    if goto and goto not in C:
                        C.append(goto)

            # 如果此次循环没有添加任何新的项集到C中，说明项集族已经完全构建完成
            if item_len == len(C):
                # 可以在这里打印完整的项集族C，以便调试或查看
                # print the canonical collection
                return C


    def construct_table(self):
        # 初始化解析表。每个项集一个状态，每个状态对应所有符号的动作为空字符串
        parse_table = {
            r: {c: "" for c in self.parse_table_symbols} for r in range(len(self.C))
        }

        # 遍历所有项集（每个项集对应一个状态）
        for i, I in enumerate(self.C):
            # 遍历项集中的每个产生式
            for head, bodies in I.items():
                for body in bodies:
                    # CASE 2 a: 处理ACTION表中的移进动作
                    if "." in body[:-1]:  # 如果点不在产生式的末尾
                        symbol_after_dot = body[body.index(".") + 1]  # 点后的符号

                        # 如果点后的符号是终结符，则计算移进动作
                        if symbol_after_dot in self.G_prime.terminals:
                            # 找到对应的转移状态
                            s = f"s{self.C.index(self.GOTO(I, symbol_after_dot))}"

                            # 避免同一单元格内有多种动作（避免冲突）
                            if s not in parse_table[i][symbol_after_dot]:
                                if "r" in parse_table[i][symbol_after_dot]:
                                    parse_table[i][symbol_after_dot] += "/"

                                parse_table[i][symbol_after_dot] += s

                    # CASE 2 b: 处理ACTION表中的规约动作
                    elif body[-1] == "." and head != self.G_prime.start:  # 如果点在产生式末尾，且不是扩展文法的起始产生式
                        for j, (G_head, G_body) in enumerate(self.G_indexed):
                            if G_head == head and (
                                G_body == body[:-1]
                                or G_body == ("^",) and body == (".",)
                            ):
                                # 遍历FOLLOW集，添加规约动作
                                for f in self.follow[head]:
                                    if parse_table[i][f]:
                                        parse_table[i][f] += "/"

                                    parse_table[i][f] += f"r{j}"

                                break

                    # CASE 2 c: 处理接受动作
                    else:  
                        parse_table[i]["$"] = "acc"

            # CASE 3: 填充GOTO表
            for A in self.G_prime.nonterminals:
                j = self.GOTO(I, A)
                if j in self.C:
                    parse_table[i][A] = self.C.index(j)

        return parse_table


    def print_info(self):
        # 定义一个辅助函数，用于格式化打印集合类型的变量
        def fprint(text, variable):
            print(f'{text:>12}: {", ".join(variable)}')

        # 打印增广文法
        print("AUGMENTED GRAMMAR:")
        for i, (head, body) in enumerate(self.G_indexed):
            # 打印每个产生式，前面加上编号
            print(f'{str(i)}: {head} -> {" ".join(body)}')

        print()
        # 打印所有的项集（Canonical Collection of LR(0) Items）
        print(" COLLECTION of ITEMS:")
        for i, productions in enumerate(self.C):
            print("----I" + str(i) + "----")  # 每个项集的标签
            for P in productions:
                for NT in productions[P]:
                    # 打印项集中的每个产生式
                    print(P, "->", " ".join(NT))

            print()

        # 打印终结符和非终结符
        fprint("TERMINALS", self.G_prime.terminals)
        fprint("NONTERMINALS", self.G_prime.nonterminals)
        fprint("SYMBOLS", self.G_prime.symbols)

        # 打印FIRST集
        print("\nFIRST:")
        for head in self.G_prime.grammar:
            print(f'{head} = {{ {", ".join(self.first[head])} }}')

        # 打印FOLLOW集
        print("\nFOLLOW:")
        for head in self.G_prime.grammar:
            print(f'{head} = {{ {", ".join(self.follow[head])} }}')

        # 打印解析表
        headers = ["ACTION"] * (1 + len(self.G_prime.terminals)) + ["GOTO"] * (
            len(self.G_prime.nonterminals) - 1
        )
        print("\nPARSING TABLE:")
        print()
        PARSE_TABLE = pd.DataFrame(self.parse_table).T
        PARSE_TABLE.columns = [headers, list(PARSE_TABLE.columns)]
        print(PARSE_TABLE)


    def LR_parser(self, w):
        # 初始化解析过程所需的变量
        buffer = f"{w} $".split()  # 将输入字符串分割成符号，并在末尾加上结束符'$'
        pointer = 0  # 输入缓冲区的指针
        a = buffer[pointer]  # 当前读入的符号
        stack = ["0"]  # 解析栈，初始化时只有状态0
        symbols = [""]  # 符号栈，与解析栈同步记录路径
        results = {  # 存储解析过程的各种信息
            "step": [],
            "stack": [] + stack,
            "symbols": [] + symbols,
            "input": [],
            "action": [],
        }

        step = 0  # 步骤编号
        while True:
            s = int(stack[-1])  # 当前状态
            step += 1
            results["step"].append(f"({step})")
            results["input"].append(" ".join(buffer[pointer:]))  # 当前输入符号串

            # 解析动作判断逻辑
            if a not in self.parse_table[s]:
                # 当前符号不在解析表中，报错退出
                results["action"].append(f"ERROR: unrecognized symbol {a}")
                break

            elif not self.parse_table[s][a]:
                # 当前状态和符号组合在解析表中没有对应动作，报错退出
                results["action"].append("ERROR: input cannot be parsed by given grammar")
                break

            elif "/" in self.parse_table[s][a]:
                # 解析表中存在冲突（移进-规约冲突或规约-规约冲突）
                action = "reduce" if self.parse_table[s][a].count("r") > 1 else "shift"
                results["action"].append(f"ERROR: {action}-reduce conflict at state {s}, symbol {a}")
                break

            elif self.parse_table[s][a].startswith("s"):
                # 移进动作
                results["action"].append("shift")
                stack.append(self.parse_table[s][a][1:])  # 移进到新的状态
                symbols.append(a)  # 记录符号
                results["stack"].append(" ".join(stack))
                results["symbols"].append(" ".join(symbols))
                pointer += 1
                a = buffer[pointer]  # 读取下一个输入符号

            elif self.parse_table[s][a].startswith("r"):
                # 规约动作
                head, body = self.G_indexed[int(self.parse_table[s][a][1:])]
                results["action"].append(f'reduce by {head} -> {" ".join(body)}')

                if body != ("^",):
                    # 如果不是由空产生式规约，则弹出栈中对应符号的数量
                    stack = stack[: -len(body)]
                    symbols = symbols[: -len(body)]

                # 根据规约完成后，根据产生式头部找到下一个状态，并更新栈和符号栈
                stack.append(str(self.parse_table[int(stack[-1])][head]))
                symbols.append(head)
                results["stack"].append(" ".join(stack))
                results["symbols"].append(" ".join(symbols))

            elif self.parse_table[s][a] == "acc":
                # 接受动作，解析成功
                results["action"].append("accept")
                break

        return results


    def print_LR_parser(self, results):
        # 使用pandas库将解析结果字典转换为DataFrame，便于格式化和展示
        df = pd.DataFrame(results)
        # 设置DataFrame的样式，这里尝试设置边框样式，但应注意这个样式设置可能不会在所有环境中有效
        # 这里的样式设置尝试给表格设置一个10像素的黄色边框，但实际上这种样式更改在标准的控制台中是不可见的，
        # 它只在支持CSS样式的环境中有效，如Jupyter Notebook。
        df.style.set_table_styles(
            [{"selector": "", "props": [("border", "10px solid yellow")]}]
        )
        # 打印一个空行以增加输出间隔
        print("\n")
        # 打印DataFrame
        print(df)

# 定义文件名，该文件包含语法定义
filename = "testGrammar.txt"

# 打开并读取文件内容
with open(filename, "r") as f:
    file_contents = f.readlines()  # 读取所有行到列表
    # 将读取的内容（列表形式）转换为单个字符串，同时过滤掉空行
    grammar_str = "".join(filter(None, file_contents))

# 使用读取到的语法字符串创建一个Grammar对象
G = Grammar(grammar_str)

# 使用Grammar对象创建一个SLRParser对象
slr_parser = SLRParser(G)
# 打印出SLR解析器的相关信息，如增广文法、项集、FIRST集、FOLLOW集等
slr_parser.print_info()

# 定义要解析的TOKEN字符串
TOKEN = "id * ( id + id )"

# 使用SLR解析器解析TOKEN字符串
results = slr_parser.LR_parser(TOKEN)
# 打印出解析结果，显示每一步的状态和动作
slr_parser.print_LR_parser(results)
