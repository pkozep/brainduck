import re
from sys import argv

"""
    Ответы на некоторые вопросы:
    1) Возникает некоторая путаница потому что, когда размер переменных (sizeVar)
    равен 1 на деле выделяется 2 ячейки памяти, когда равен 2 выделяеться 4 и т.д.
    Это происходит потому что, операция копирования значения из ячейки требует
    использовать буферную ячейку, и в целях оптимизации работы программы
    была выбрана такая архитектура работы с памятью, тоесть каждому полезному байту памяти
    соответствует 1 байт памяти, необходиый чтобы скопировать значение этого байта.
    2) Для работы с отрицательными числами используется беззнаковая запись
    иными словами для положительных значений выделены числа от 0 до 128 а для отрицательных от 129 до 255
    3) Важный приниц, в коде BF++ есть вариантивность, а следовательно
    для возможности поиска курсора необходимо ограничить эту вариантивность строгим правилом
    КАЖДЫЙ БЛОК КОДА С СЛОВИЯМИ ДОЛЖЕН ЗАКАНЧИВАТЬСЯ В ОДНОЙ И ТОЙЖЕ ЯЧЕЙКЕ НЕ ЗАВИСИМО ОТ ВЫПОЛНЕНИЯ УСЛОВИЙ
"""

class BD:
    def __init__( self ) -> None:   
        self.last_gen_name = 0  # Это счётчик для того, чтобы генерируемые переменные имели уникальное имя
        self.memory = [] # Это список занятых ячеек памяти
        self.code = "" # Это результирующий код на BF++ 
    
    def get_memory( self, nameVar: str, sizeVar: int = 1 ) -> int: # Метод резервирует необходимое количество ячеек за переменой и возвращает индекс первой ячейки
        free_start, free_count = -1, 0
        for i, isOccupied in enumerate( self.memory ):
            if not isOccupied:
                free_count += 1
                if free_count == sizeVar:
                    free_start = i - sizeVar + 1
                    break
            else:
                free_count = 0
        
        if free_start == -1:
            free_start = len( self.memory )
            self.memory.extend( [False] * sizeVar )
        for i in range( free_start, free_start + sizeVar ):
            self.memory[i] = nameVar
        
        return self.memory.index( nameVar ) * 2
    
    def get_variable_index( self, nameVar: str ) -> int:
        return self.memory.index( nameVar ) * 2 # Почему индекс * 2 можно прочитать в ответах №1
        
    def del_variable( self, nameVar: str ) -> None: # Освобождает ячейки занятые переменной nameVar
        for i in range( len( self.memory ) ):
            if self.memory[i] == nameVar:
                self.memory[i] = False
                self.clear_value( i*2 )
        self.optimize()
    
    def gen_variable( self ) -> (str, int): # Генерирует переменную, которая будет использоваться в качестве буферной переменной
        self.last_gen_name += 1
        name = 'gen_' + str( self.last_gen_name ).zfill( 6 )
        return name, self.get_memory( name )

    def optimize( self ) -> None: #  Удаляет подрят стоящие в конце пустые переменные, нужно для оптимизации
        while self.memory and self.memory[-1] == False:
            self.memory = self.memory[:-1]

    # Метод преобразует фрагмент кода в последовательность комманд
    # Понимать как работает этот метод не обязательно, так как
    # его цель всего лишь преобразовать текстовый фрагмент кода в последовательность команд
    def render_fragment( self, fragment: str ) -> list:
        commands = []
        word = ""
        brace_count = 0
        for char in fragment:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
            elif char == ';' and brace_count == 0 and word:
                commands.append( word )
                word = ""
                continue
            word += char
        return commands

    # Метод исполняет список команд
    def render_code( self, code ):
        clean_code = code[1:-2].replace( '  ', '' ).replace( '\n', '' )
        commands = self.render_fragment( clean_code )
        for command in commands:
            self.execution(command)
        return self.code

    # Метод выполняет команду на высоком уровне, то есть он
    # оперирует лишь методами brainduck
    def execution( self, command, indent: int = 0 ) -> None:
        print( '    ' * indent, command ) # Это нужно для отладки, потом удалить
        
        # Следующий метод реализует вычисление значения выражения expression
        # Результат присваевается к значению в ячейке var_ind
        ### Нужно доработать этот метод, что бы он верно трактовал последовательность операций 
        def handle_simple_assignment( var_ind: int, expression: str ) -> None:
            if re.fullmatch( r"\d+", expression ):  # Обработка целого положительного значения от 0 до 128
                self.set_value( var_ind, int( expression ) )
            elif re.fullmatch( r"\'[ -~]\'", expression ):  # Обработка символа ASCII
                self.set_value( var_ind, ord( expression[1] ) )
            elif re.fullmatch( r"\w+", expression ):    # Обработка переменных
                self.clear_value( var_ind )
                self.copy( self.get_variable_index( expression ), var_ind )
            elif re.fullmatch( r".+ [!=]= .+", expression ): # Обработка равенств двух аргументов
                op1, op2 = re.split( r" [!=]= ", expression )
                operation = re.findall( r"[!=]=", expression )[0]
                tmp1, tmp1_ind = self.gen_variable()
                tmp2, tmp2_ind = self.gen_variable()
                handle_simple_assignment( tmp1_ind, op1 )
                handle_simple_assignment( tmp2_ind, op2 )
                self.clear_value( var_ind )
                if operation == "==":
                    self.equality( tmp1_ind, tmp2_ind, var_ind )
                else:
                    self.equality( tmp1_ind, tmp2_ind, var_ind, False )
                self.del_variable( tmp1 ), self.del_variable( tmp2 )
            elif re.fullmatch( r".+ [><] .+", expression ): # Обработка строгих неравенств
                op1, op2 = re.split( r" [><] ", expression )
                operation = re.findall( r"[><]", expression )[0]
                arg1, arg1_ind = self.gen_variable()
                arg2, arg2_ind = self.gen_variable()
                handle_simple_assignment( arg1_ind, op1 )
                handle_simple_assignment( arg2_ind, op2 )
                self.clear_value( var_ind )
                if operation == '>':
                    self.comparison( arg1_ind, arg2_ind, var_ind )
                else:
                    self.comparison( arg2_ind, arg1_ind, var_ind )
                self.del_variable( arg1 ), self.del_variable( arg2 )
            elif re.fullmatch( r".+ [><]= .+", expression ): # Обработка нестрогих неравенств
                op1, op2 = re.split( r" [><]= ", expression )
                operation = re.findall( r"[><]", expression )[0]
                arg1, arg1_ind = self.gen_variable()
                arg2, arg2_ind = self.gen_variable()
                handle_simple_assignment( arg1_ind, op1 )
                handle_simple_assignment( arg2_ind, op2 )
                self.clear_value( var_ind )
                if operation == '>':
                    self.comparison( arg2_ind, arg1_ind, var_ind, False )
                else:
                    self.comparison( arg1_ind, arg2_ind, var_ind, False )
                self.del_variable( arg1 ), self.del_variable( arg2 )
            elif re.fullmatch( r".+ [\+\-\*/] .+", expression ): # Обработка математических операция (+-*/) для двух аргументов
                op1, op2 = re.split( r" [\+\-\*/] ", expression )
                operation = re.findall( r"[\+\-\*/]", expression )[0]
                tmp, tmp_ind = self.gen_variable()
                if operation == '+':
                    arg1, arg1_ind = self.gen_variable()
                    arg2, arg2_ind = self.gen_variable()
                    handle_simple_assignment( arg1_ind, op1 )
                    handle_simple_assignment( arg2_ind, op2 )
                    self.clear_value( var_ind )
                    self.move( arg1_ind, var_ind )
                    self.move( arg2_ind, var_ind )
                    self.del_variable( arg1 ), self.del_variable( arg2 )
                elif operation == '-':
                    arg1, arg1_ind = self.gen_variable()
                    arg2, arg2_ind = self.gen_variable()
                    handle_simple_assignment( arg1_ind, op1 )
                    handle_simple_assignment( arg2_ind, op2 )
                    self.clear_value( var_ind )
                    self.move( arg1_ind, var_ind )
                    self.move( arg2_ind, var_ind, False)
                    self.del_variable( arg1 ), self.del_variable( arg2 )
                elif operation == '*':
                    handle_simple_assignment( tmp_ind, op1 )
                    arg, arg_ind = self.gen_variable()
                    handle_simple_assignment( arg_ind, op2 )
                    self.cycle( tmp_ind, [
                        [ self.add_value, -1 ],
                        [ handle_simple_assignment, arg_ind, op2 ]
                    ] )
                    self.clear_value( var_ind )
                    self.move( arg_ind, var_ind )
                elif operation == '/':
                    tmp1, tmp1_ind = self.gen_variable()
                    tmp2, tmp2_ind = self.gen_variable()
                    handle_simple_assignment( tmp1_ind, op1 )
                    handle_simple_assignment( tmp2_ind, op2 )
                    handle_simple_assignment( tmp_ind, tmp1 + " - " + tmp2 + " <= 128" )
                    self.cycle( tmp_ind, [
                        [ self.copy, tmp2_ind, tmp1_ind, False ],
                        [ handle_simple_assignment, tmp_ind, tmp1 + " - " + tmp2 + " <= 128" ],
                        [ self.set_cursor, var_ind ],
                        [ self.add_value, 1 ]
                    ] )
                    self.del_variable( tmp1 ), self.del_variable( tmp2 )
                self.del_variable( tmp )
            else:
                print( f"Выражение не обработано: \"{ expression }\"" )
            
        # Следующие обработчики являются первичными обработчиками команд BrainDuck
        if re.fullmatch( r"det\d+ \w+", command ):   # det1 a
            size, name = command[3:].split()
            var_ind = self.get_memory( name, int( size ) )
        elif re.fullmatch( r"det\d+ \w+ = .*", command ):  # det a = ...
            size_and_name, expression = re.split( " = ", command[3:], maxsplit=1 )
            size, name = size_and_name.split()
            self.execution( f"det{size} {name}", indent + 1 )
            self.execution( f"{name} = {expression}", indent + 1 )
        elif re.fullmatch( r"\w+ = .*", command ):  # a = ...
            name, expression = re.split( ' = ', command, maxsplit=1 )
            var_ind = self.get_variable_index( name )
            tmp, tmp_ind = self.gen_variable()
            handle_simple_assignment( tmp_ind, expression )
            self.move( tmp_ind, var_ind )
            self.del_variable( tmp ) # Не очищаю tmp_ind, так как последняя команда move и так обнуляет его
        elif re.fullmatch( r"\w+ [\+\-\*/]= .*", command ):  # a += ...
            name, expression = re.split( r' [\+\-\*/]= ', command, maxsplit=1 )
            operation = re.findall( r' [\+\-\*/]= ', command )[0][1]
            self.execution( f"{name} = {name} {operation} {expression}", indent + 1 )
        elif re.fullmatch( r"if .+ \{.*\}", command ): # if ... {...; ...;}
            cond, body = re.split( r' \{', command[3:], maxsplit=1 )
            body = body.rstrip( '}' )
            tmp, tmp_ind = self.gen_variable()
            handle_simple_assignment( tmp_ind, cond )
            self.cycle( tmp_ind, [
                [ self.set_cursor, tmp_ind ],
                [ self.clear_value ]
            ] + [
                [ self.execution, render_command ] for render_command in self.render_fragment( body ) 
            ] )
            self.del_variable( tmp )
        elif re.fullmatch( r"while .+ \{.*\}", command ): # while ... {...; ...;}
            cond, body = re.split( ' {', command[6:], maxsplit=1 )
            body = body.rstrip( '}' )
            tmp, tmp_ind = self.gen_variable()
            handle_simple_assignment( tmp_ind, cond )
            self.cycle( tmp_ind, [
                [ self.execution, render_command, indent + 1 ] for render_command in self.render_fragment( body.replace( cond, tmp ) )
            ] + [
                [ self.execution, f"{tmp} = {cond}", indent + 1 ]
            ] )
            self.del_variable( tmp )
        else:
            print(f"Команда не обработана: ", command)

    # Методы работы с кодом BF++
    # Эти методы самое важное, что есть в этой программе
    def find_cursor( self ) -> int: # Это первый и самый крутой метод (это хоть кто-то читает?) он позволяет найти текущее положение курсора подробнее в ответах №3
        return self.code.count( '>' ) - self.code.count( '<' )
    
    def set_cursor( self, ind: int ) -> int: # Устанавливает курсор в ячейку с индексом ind
        cursor = self.find_cursor()
        self.code += '>' * ( ind - cursor ) + '<' * ( cursor - ind )

    def clear_value( self, ind: int ) -> None: # Обнуляет значение в текущей ячейке
        self.set_cursor( ind )
        self.code += "[-]"

    def add_value( self, value: int ) -> None: # Добавляет значение value в текущую ячейку
        self.code += '+' * value + '-' * ( -value )

    def set_value( self, ind: int, value: int ) -> None: # Устанавливает значение value в ячейку ind
        self.clear_value( ind )
        self.add_value( value )

    def cycle( self, ind: int, commands: list ) -> None: # Реализация цикла while пока ind != 0
        self.set_cursor( ind )
        self.code += '['
        for command in commands:
            command[0]( *command[1:] )
        self.set_cursor( ind ) # Эта строчка нужна по причине сказаной в ответе №3
        self.code += ']'

    def move( self, src: int, dst: int, forward: bool = True ) -> None: # Перемещает значение ячейки src в ячейку dst
        self.cycle( src, [
            [ self.add_value, -1 ],
            [ self.set_cursor, dst ],
            [ self.add_value, forward * 2 - 1 ]
        ] )

    def copy( self, src: int, dst: int, forward: bool = True ) -> None: # Копирует значение язейки src в ячейку dst
        tmp = src + 1
        self.cycle( src, [
            [ self.add_value, -1 ],
            [ self.set_cursor, tmp ],
            [ self.add_value, 1 ],
            [ self.set_cursor, dst ],
            [ self.add_value, forward * 2 - 1 ]
        ] )
        self.move( tmp, src )

    def equality( self, op1: int, op2: int, output: int, forward: bool = True ) -> None: # Сравнивает значение из ячеек op1 и op2, результат в output
        self.copy( op1, output )
        self.copy( op2, output, False )
        self.set_cursor( output )
        if forward:
            self.code += '>+<[>-<[-]]>[-<+>]'
        else:
            self.code += '[>+<[-]]>[-<+>]'

    def comparison( self, op1: int, op2: int, output: int, forward: bool = True ) -> None:  # Метод проверяет больше ли op1 чем op2
        # Этот метод позволяет вычислить два выражения
        # Если forward = True, то метод аналогичен операции op1 > op2
        # Если forward = False, то метод аналогичен операции op1 <= op2
        # Это работает так, потому что эти операции обратны друг другу
        two_byte_1, tb1_ind = self.gen_variable()
        two_byte_2, tb2_ind = self.gen_variable()
        two_byte_3, tb3_ind = self.gen_variable()
        self.set_cursor( tb1_ind )
        self.add_value( 1 )
        self.copy( op1, tb2_ind )
        self.copy( op2, tb2_ind + 1 )
        self.set_cursor( tb1_ind )
        if forward:
            self.code += ">>[[->]<<]<[->]+<[>-<-]"
        else:
            self.code += ">>[[->]<<]<[->]+<[>+<-]>-<"
        self.clear_value( tb2_ind )
        self.clear_value( tb2_ind + 1 )
        self.move( tb1_ind +  1, output )
        self.del_variable( two_byte_1 ), self.del_variable( two_byte_2 ), self.del_variable( two_byte_3 )

    def print( self ) -> None: # Выводит текущую ячейку
        self.code += '.'

    def input( self ) -> None: # Вводит значение в текущую ячейку
        self.code += ','

if __name__ == "__main__":
    for i in range(1, 4, 2):
        if len( argv ) == 5:
            if argv[i] == "-i": input_file = argv[i + 1]
            if argv[i] == "-o": output_file = argv[i + 1]
        else:
            raise "Необходимо передать -i <входной файл> и -o <выходной файд>"
        
    bd_compil = BD()
    with open( input_file, 'r', encoding="utf-8" ) as file:
        code = file.read()

    with open( output_file, 'w' ) as file:
        file.write( bd_compil.render_code( code ) + "@" )
