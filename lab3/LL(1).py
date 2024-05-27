def remove_left_recur(nonTerminals):
    # 按照字母顺序对非终结符进行排序，确保一致的处理顺序
    keys = sorted(nonTerminals.keys())
    
    # 创建一个新的字典来存储修改后的产生式
    newNonTerminals = {}

    # 查找未使用的字母作为新的非终结符
    used_keys = set(nonTerminals.keys())
    available_keys = (chr(i) for i in range(ord('A'), ord('Z') + 1) if chr(i) not in used_keys)

    for key in keys:
        productions = nonTerminals[key]
        non_recursive = []  # 用于存储非直接递归的产生式
        recursive = []      # 用于存储直接递归的产生式

        # 分离直接递归和非直接递归的产生式
        for production in productions:
            if production.startswith(key):
                # 去除左递归部分，例如 "E+T" 变成 "+T"
                recursive.append(production[len(key):].strip())
            else:
                non_recursive.append(production)

        # 如果存在直接左递归，进行处理
        if recursive:
            new_key = next(available_keys)  # 获取未使用的字母作为新非终结符
            newNonTerminals[key] = [prod + new_key for prod in non_recursive]  # 更新非递归产生式，使其以新的非终结符结尾
            newNonTerminals[new_key] = [r + new_key for r in recursive] + ['@']  # 为新的非终结符创建产生式，转换递归部分为非递归
        else:
            # 如果没有直接左递归，保持原样
            newNonTerminals[key] = productions

    # 清空原始字典，并用新的产生式集更新它
    nonTerminals.clear()
    nonTerminals.update(newNonTerminals)

    return nonTerminals



# ----------  ENDS (left _ Recur ) ----------------------





# 2. -------------- First and Follow --------------------
# Global dictionaries to hold the First and Follow sets
First = {}
Follow = {}

# 定义一个函数，计算单个产生式字符串的FIRST集合
def first4pro(production):
    fir = []  # 初始化FIRST集合
    for symbol in production:  # 遍历产生式中的每个符号
        if '@' not in First[symbol]:  # 如果当前符号的FIRST集合中不包含空串'@'
            fir.extend(First[symbol])  # 将当前符号的FIRST集合加入到fir中
            break  # 由于当前符号的FIRST集合中没有空串，停止处理后续符号
        else:
            # 将除了空串'@'外的其他符号加入到fir中
            fir.extend(x for x in First[symbol] if x != '@')
    else:
        # 如果所有符号的FIRST集合都包含空串'@'，则在最终的FIRST集合中添加'@'
        fir.append('@')
    return fir  # 返回计算得到的FIRST集合

# 定义一个递归函数来计算非终结符的FIRST集合
def first(nT, nonT, checked):
    if checked[nT]:  # 如果已经计算过当前非终结符的FIRST集合，则直接返回
        return
    checked[nT] = True  # 标记当前非终结符的FIRST集合已被计算
    First[nT] = []  # 初始化当前非终结符的FIRST集合为空列表

    for production in nonT[nT]:  # 遍历当前非终结符的所有产生式
        first_for_production = []  # 初始化当前产生式的FIRST集合为空列表

        for symbol in production:  # 遍历产生式中的每个符号
            if not checked.get(symbol, False):  # 如果当前符号是非终结符且未被计算过FIRST集
                first(symbol, nonT, checked)  # 递归计算当前符号的FIRST集

            first_for_production.extend(First[symbol])  # 将当前符号的FIRST集合加入到当前产生式的FIRST集中
            if '@' not in First[symbol]:  # 如果当前符号的FIRST集合中不包含空串'@'
                break  # 停止处理后续符号
        else:
            # 如果所有符号的FIRST集合都包含空串'@'，则在当前产生式的FIRST集合中添加'@'
            first_for_production.append('@')

        # 将当前产生式的FIRST集合中的唯一项添加到当前非终结符的FIRST集合中
        First[nT].extend(x for x in first_for_production if x not in First[nT])

# 定义一个函数初始化FIRST集合，并计算所有非终结符的FIRST集
def createFirst(terminals, nonT):
    checked = {term: True for term in terminals}  # 终结符的FIRST集合就是它们自身
    for term in terminals:
        First[term] = [term]  # 初始化每个终结符的FIRST集合为包含自身的列表

    for nonTerm in nonT:
        checked[nonTerm] = False  # 初始化所有非终结符的检查状态为未检查

    for nonTerm in nonT:
        if not checked[nonTerm]:  # 如果有非终结符未被检查
            first(nonTerm, nonT, checked)  # 计算该非终结符的FIRST集

    # 可选：去除FIRST集中的重复项（上面的代码已通过集合操作避免了重复）
    for key in First:
        First[key] = list(set(First[key]))


    #(ii) ------- Follow------------
# 定义一个递归函数计算非终结符的FOLLOW集
def follow(nT, nonT, checked):
    if checked[nT]:  # 如果已经计算过当前非终结符的FOLLOW集，则直接返回
        return
    checked[nT] = True  # 标记当前非终结符的FOLLOW集正在被计算
    if nT not in Follow:
        Follow[nT] = []  # 如果当前非终结符的FOLLOW集还未初始化，则初始化为空列表

    # 遍历所有产生式，寻找当前非终结符nT出现的地方
    for head, productions in nonT.items():
        for production in productions:
            # 找出产生式中所有nT的位置
            positions = [i for i, symbol in enumerate(production) if symbol == nT]
            for pos in positions:
                # 检查nT后面是否还有符号
                if pos + 1 < len(production):
                    next_symbol = production[pos + 1]
                    # 将next_symbol的FIRST集中除了空串'@'外的所有符号加到nT的FOLLOW集中
                    Follow[nT].extend(x for x in First[next_symbol] if x != '@')
                    # 如果next_symbol的FIRST集中包含空串'@'，则将产生式左边非终结符head的FOLLOW集加到nT的FOLLOW集中
                    if '@' in First[next_symbol]:
                        follow(head, nonT, checked)  # 递归确保计算head的FOLLOW集
                        Follow[nT].extend(Follow[head])
                else:
                    # 如果nT在产生式中是最后一个符号，直接将head的FOLLOW集加到nT的FOLLOW集中
                    follow(head, nonT, checked)  # 递归确保计算head的FOLLOW集
                    Follow[nT].extend(Follow[head])

# 定义一个函数初始化FOLLOW集，并为每个非终结符计算FOLLOW集
def createFollow(terminals, nonT, start_symbol):
    checked = {nt: False for nt in nonT}  # 初始化标记，用于追踪每个非终结符的FOLLOW集是否已计算
    for nt in nonT:
        Follow[nt] = []  # 为每个非终结符初始化FOLLOW集为空列表
    Follow[start_symbol] = ['$']  # 文法的起始符号的FOLLOW集总是包含结束符'$'

    # 遍历每个非终结符，如果其FOLLOW集未计算，则进行计算
    for nt in nonT:
        if not checked[nt]:
            follow(nt, nonT, checked)

    # 清理FOLLOW集，去除重复项，并确保不包含空串'@'
    for nt in Follow:
        Follow[nt] = list(set(Follow[nt]))  # 去除重复项
        if '@' in Follow[nt]:
            Follow[nt].remove('@')  # 如果误将空串'@'加入，则移除之

    

# ----------------- ENDS(F and F) ------------------------





# 3. --------------------- Parse Table --------------------
# 初始化解析表、终结符映射和非终结符映射
parseTable = list()
terMap = dict()
nonTMap = dict()

# 定义创建解析表的函数
def createParseTable(ter, nonT, First, Follow):
    # 遍历所有非终结符
    for i in nonT.keys():
        # 遍历当前非终结符的每个产生式
        for j in nonT[i]:
            # 调用first4pro函数计算当前产生式的FIRST集
            fir = first4pro(j)
            # 对于FIRST集中的每个元素
            for k in fir:
                if k != '@':  # 如果元素不是空串
                    # 在解析表中为非终结符i和终结符k设置产生式
                    parseTable[nonTMap[i]][terMap[k]] = str(i) + str(j)
                else:
                    # 如果元素是空串'@'，则需要查看FOLLOW集
                    for tr in Follow[i]:
                        # 对FOLLOW集中的每个终结符，设置产生式为当前非终结符到空串的映射
                        parseTable[nonTMap[i]][terMap[tr]] = str(i) + str('@')

    

    

# ----------------------------ENDS(Parse Table) -----------






# 4. ------------------------Traversal ---------------

# (i) ----- Stack -----------------
class Stack:
    def __init__(self):
        self.__storage = []

    def isEmpty(self):
        return len(self.__storage) == 0

    def push(self,p):
        self.__storage.append(p)

    def pop(self):
        return self.__storage.pop()
    def top(self):
        return self.__storage[len(self.__storage) - 1]
    def __str__(self):
        return 'stack [{}]'.format(', '.join([ str(i) for i in reversed(self.__storage) ]))
    
#----------------------ENDS(Traversal) --------------------







#---------------- Driver Program ------------------------
#---------------- 驱动程序 ------------------------

# 初始化终结符列表和非终结符字典
terminals = []
nonTerminals = dict()

# 用户输入终结符，以逗号分隔
terminals = input("Enter Terminals (,) : ").split(",")

# 输入非终结符的数量
n = int(input("No. of Non - Terminals  : "))

# 根据用户输入，收集每个非终结符及其产生式
for i in range(n):
    ch = input("NonTerminals : ").strip()  # 输入非终结符
    rules = input("Productions (,) : ").split(",")  # 输入产生式，以逗号分隔
    nonTerminals[ch] = rules  # 将产生式分配给对应的非终结符

# 获取文法的开始符号
S = input("Start Symbol :  ")
# 在终结符列表中添加'$'（输入结束符）和'@'（空串符号）
terminals += ['$', '@']

# 打印输入的产生式规则
print("Productions : ")
for i in nonTerminals.keys():
    print(i, "-->", end=' ')
    for j in nonTerminals[i]:
        print(j, end=' | ')
    print()

# 调用函数remove_left_recur来处理非终结符的左递归
remove_left_recur(nonTerminals)

# 打印处理左递归后的产生式
print("\nAfter Left Recurions Productions : ")
for i in nonTerminals.keys():
    print(i, "-->", end=' ')
    for j in nonTerminals[i]:
        print(j, end=' | ')
    print()

# 调用createFirst函数计算每个非终结符的FIRST集
createFirst(terminals, nonTerminals)

# 调用createFollow函数计算每个非终结符的FOLLOW集，传入开始符号
createFollow(terminals, nonTerminals, S)

# 打印每个非终结符的Grammar Rule、First集和Follow集
print("{}\t\t\t\t{}\t\t\t\t{}".format('Grammar Rule', 'First', 'Follow'))
for i in nonTerminals.keys():
    print("{}\t\t\t\t{}\t\t\t\t{}".format(i, First[i], Follow[i]))

# -------- 解析表的准备工作将在此处继续 --------


#-------- Parse Table ----------------
# 初始化解析表

# 为每个终结符创建映射，映射它们到一个唯一的索引
for count, i in enumerate(terminals):
    terMap[i] = count + 1

# 为每个非终结符创建映射，映射它们到一个唯一的索引
for count, i in enumerate(nonTerminals.keys()):
    nonTMap[i] = count + 1

# 创建一个二维数组作为解析表，其大小为非终结符数量加一乘以终结符数量加一
# 初始化表中的所有元素为0，表示没有对应的产生式
parseTable = [[0 for _ in range(len(terminals) + 1)] for _ in range(len(nonTerminals.keys()) + 1)]
print(terMap, "\n", nonTMap)  # 打印终结符和非终结符的映射

# 初始化完成

# 调用createParseTable函数填充解析表
createParseTable(terminals, nonTerminals, First, Follow)

# 打印解析表的表头，显示所有终结符
print(end='\t\t ')
for i in terminals:
    print(i, end='\t\t  ')
print()  # 换行

# 打印解析表的每一行，每一行对应一个非终结符及其对应终结符的产生式索引
for i in list(nonTerminals.keys()):
    print(i, end='\t\t')  # 打印非终结符
    for j in terminals:
        # 根据映射找到解析表中的具体位置并打印值
        print(parseTable[nonTMap[i]][terMap[j]], end='\t\t')
    print()  # 每打印完一行后换行

#--------------- Parse Table Done ---------------




#------------ Traversals :-----------------------

string = input("String to Parse :  ")
st = Stack()

st.push('$')
st.push(S)  # Start Symbol

i = 0
# while循环继续执行，直到i不再小于字符串string的长度
while(i < len(string)):
    print(st, " Exp : ", string[i])  # 打印当前栈和正在处理的字符

    # 如果当前字符不是终结符，则退出循环
    if string[i] not in terminals:
        break
    # 如果栈顶是空串'@'（表示epsilon或空产生），则弹出栈顶
    elif not st.isEmpty() and st.top() == '@':
        st.pop()
    # 如果栈顶元素与当前处理的字符相同，则弹出栈顶并移动索引到下一个字符
    elif not st.isEmpty() and st.top() == string[i]:
        st.pop()
        i += 1
    # 如果栈顶是一个非终结符
    elif not st.isEmpty() and st.top() in nonTerminals.keys():
        # 查找解析表中对应的条目，如果为0，则无法继续解析，退出循环
        if parseTable[nonTMap[st.top()]][terMap[string[i]]] == 0:
            break
        else:
            c = st.pop()  # 弹出栈顶非终结符
            # 解析表返回的产生式（去掉首字符后）反转后依次推入栈中
            for j in str(parseTable[nonTMap[c]][terMap[string[i]]])[1:][::-1]:
                st.push(j)

# 如果栈为空，表示输入字符串被成功解析
if st.isEmpty():
    print("Successfully Parsed")
else:
    # 如果栈不为空，表示解析过程中遇到错误，输入字符串不符合语法规则
    print("Unsuccessful Attempt")
